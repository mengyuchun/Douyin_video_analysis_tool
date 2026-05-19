"""大模型结构化输出模块 - 分析文本并生成结构化结果"""
import asyncio
import json
import re
from datetime import datetime
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.config import load_config, init_data_dirs

console = Console()

# ==================== 内置提示词模板 ====================

PROMPT_TEMPLATES = {
    "content_summary": {
        "name": "内容摘要",
        "prompt": """请对以下短视频文案进行结构化分析，输出JSON格式：

{
  "title": "视频标题(一句话概括)",
  "summary": "内容摘要(50-100字)",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "category": "内容类别(如: 知识分享/娱乐搞笑/生活日常/商品推广等)",
  "sentiment": "情感倾向(正面/中性/负面)",
  "highlights": ["亮点1", "亮点2"],
  "target_audience": "目标受众"
}

视频文案内容：
"""
    },
    "product_analysis": {
        "name": "带货分析",
        "prompt": """请对以下带货类短视频文案进行结构化分析，输出JSON格式：

{
  "product_name": "商品名称",
  "product_category": "商品类别",
  "selling_points": ["卖点1", "卖点2", "卖点3"],
  "price_info": "价格信息(如有提及)",
  "promotion_method": "推广方式(如: 口播推荐/使用演示/对比测试)",
  "target_audience": "目标用户画像",
  "conversion_hooks": ["转化钩子1", "转化钩子2"],
  "effectiveness_score": 8,
  "suggestions": "改进建议"
}

视频文案内容：
"""
    },
    "sentiment_analysis": {
        "name": "情感分析",
        "prompt": """请对以下短视频文案进行情感分析，输出JSON格式：

{
  "overall_sentiment": "整体情感(正面/中性/负面)",
  "sentiment_score": 0.8,
  "emotion_tags": ["开心", "感动", "期待"],
  "key_emotions": [
    {"text": "触发情感的文本片段", "emotion": "情感类型", "intensity": "强度"}
  ],
  "audience_reaction_predict": "预期观众反应"
}

视频文案内容：
"""
    },
    "custom": {
        "name": "自定义",
        "prompt": ""
    },
    "video_analysis": {
        "name": "视频带货分析",
        "prompt": """你是一位有二十年从业经验的顶级的中国出版营销专家和短视频拆解分析师。
该短视频正在带货或宣传的图书名称是：《{book_title}》。

【任务说明】
请根据我提供的视频台词，严格以 JSON 格式输出分析结果。你的分类选择必须从我给定的选项中挑选，并在 Reason 字段给出充分的依据（引用原句）。
注意：博主可能不会直接说出书名，而是用"这本书"、"左下角"等指代。

【前三句台词】：
{hook_text}

【完整台词】：
{full_text}

【输出格式要求（必须是合法的纯 JSON 对象，不要输出 markdown 标记如 ```json）】
{{
    "Hook_Type": "只能从 [痛点提问 / 认知颠覆 / 故事代入 / 平铺直叙 / 其他（待人工核查）] 中选择",
    "Hook_Reason": "原句引用，并说明为什么选这个钩子标签",
    "CTA_Softness": "只能从 [硬广逼单 / 利益诱导 / 情绪软植入 / 无转化 / 其他（待人工核查）] 中选择",
    "CTA_Reason": "摘抄出明确引导购买或点名书名的原句，若无则说明",
    "Core_Emotion": "只能从 [制造焦虑 / 共情治愈 / 鸡血赋能 / 其他（待人工核查）] 中选择",
    "Emotion_Reason": "简述整个脚本的情绪流向依据",
    "Narrative_Structure": "只能从 [PAS(痛点-放大-方案) / 故事讲述-升华 / 认知科普-推销 / 纯硬广罗列 / 其他（待人工核查）] 中选",
    "Structure_Reason": "简述脚本的起承转合逻辑"
}}
"""
    }
}


# ==================== 大模型API调用 ====================

class DashScopeProvider:
    """阿里云百炼 DashScope（OpenAI兼容模式）"""

    def __init__(self, api_key: str, model: str = "qwen3.5-flash"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    async def chat(self, prompt: str, content: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt + content}],
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            raise Exception(f"DashScope调用失败: {data.get('error', {}).get('message', '未知错误')}")


class OpenAIProvider:
    """OpenAI兼容接口(支持国内中转)"""

    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def chat(self, prompt: str, content: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt + content}],
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            raise Exception(f"OpenAI调用失败: {data.get('error', {}).get('message', '未知错误')}")


class OllamaProvider:
    """本地 Ollama 大模型（无需API Key）"""

    def __init__(self, base_url: str = "http://localhost:11434/v1", model: str = "gemma4:e4b"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def chat(self, prompt: str, content: str) -> str:
        async with httpx.AsyncClient(timeout=300) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt + content}],
                },
                headers={"Content-Type": "application/json"},
            )
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            raise Exception(f"Ollama调用失败: {data.get('error', '未知错误')}")


def get_llm_provider():
    """根据配置返回大模型实例"""
    config = load_config()
    provider = config.get("llm_provider", "ollama")
    api_key = config.get("llm_api_key", "")
    model = config.get("llm_model", "")

    if provider == "dashscope":
        if not api_key:
            raise Exception("请在config.json中配置 llm_api_key（阿里云百炼API Key）")
        return DashScopeProvider(api_key, model or "qwen3.5-flash")
    elif provider == "ollama":
        base_url = config.get("ollama_base_url", "http://localhost:11434/v1")
        ollama_model = config.get("ollama_model", "gemma4:e4b")
        return OllamaProvider(base_url, ollama_model)
    elif provider == "openai":
        if not api_key:
            raise Exception("请在config.json中配置 llm_api_key")
        base_url = config.get("llm_base_url", "https://api.openai.com/v1")
        return OpenAIProvider(api_key, model or "gpt-3.5-turbo", base_url)
    else:
        raise Exception(f"不支持的大模型提供商: {provider}，可选: dashscope / ollama / openai")


# ==================== 结果保存 ====================

def save_json(result: dict, text_path: str) -> str:
    """保存JSON结果到 data/analysis/"""
    text_path = Path(text_path)
    dirs = init_data_dirs()
    output_path = dirs["analysis"] / f"{text_path.stem}_分析结果.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return str(output_path)


def save_markdown(result: dict, text_path: str, template_name: str) -> str:
    """保存Markdown报告到 data/analysis/"""
    text_path = Path(text_path)
    dirs = init_data_dirs()
    output_path = dirs["analysis"] / f"{text_path.stem}_分析报告.md"

    lines = [
        f"# 分析报告: {text_path.stem}",
        "",
        f"- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 分析模板: {template_name}",
        "",
        "---",
        "",
    ]

    for key, value in result.items():
        lines.append(f"## {key}")
        lines.append("")
        if isinstance(value, list):
            for item in value:
                lines.append(f"- {item}")
        elif isinstance(value, dict):
            for k, v in value.items():
                lines.append(f"- **{k}**: {v}")
        else:
            lines.append(str(value))
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(output_path)


def parse_llm_output(text: str) -> dict:
    """从LLM输出中提取JSON"""
    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试从```json...```中提取
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # 尝试从{...}中提取
    brace_match = re.search(r'\{.*\}', text, re.DOTALL)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    # 解析失败，返回原始文本
    return {"raw_output": text}


# ==================== 主流程 ====================

async def analyze_single(llm_provider, text_path: str, prompt_template: str, template_name: str) -> bool:
    """分析单个文本文件"""
    try:
        text_path = Path(text_path)
        console.print(f"[blue]正在分析: {text_path.name}[/blue]")

        # 读取文本内容
        with open(text_path, "r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            console.print(f"[yellow]文本为空，跳过: {text_path.name}[/yellow]")
            return False

        # 调用大模型
        response = await llm_provider.chat(prompt_template, content)

        # 解析输出
        result = parse_llm_output(response)

        config = load_config()

        # 保存JSON
        if config.get("output_json", True):
            json_path = save_json(result, str(text_path))
            console.print(f"[green]  JSON: {Path(json_path).name}[/green]")

        # 保存Markdown
        if config.get("output_markdown", True):
            md_path = save_markdown(result, str(text_path), template_name)
            console.print(f"[green]  报告: {Path(md_path).name}[/green]")

        return True

    except Exception as e:
        console.print(f"[red]分析失败 {Path(text_path).name}: {e}[/red]")
        return False


async def batch_analyze(text_files: list[str]) -> list[str]:
    """批量分析文本文件

    Args:
        text_files: 文本文件路径列表

    Returns:
        生成的结果文件路径列表
    """
    if not text_files:
        console.print("[yellow]没有文本文件需要分析[/yellow]")
        return []

    # 选择提示词模板
    console.print("\n[bold]请选择分析模板:[/bold]")
    template_keys = list(PROMPT_TEMPLATES.keys())
    for i, key in enumerate(template_keys, 1):
        console.print(f"  {i}. {PROMPT_TEMPLATES[key]['name']}")

    choice = console.input("\n请输入编号 (默认1): ").strip() or "1"
    try:
        idx = int(choice) - 1
        template_key = template_keys[idx]
    except (ValueError, IndexError):
        template_key = "content_summary"

    template_info = PROMPT_TEMPLATES[template_key]
    prompt_template = template_info["prompt"]

    # 自定义提示词
    if template_key == "custom":
        console.print("[yellow]请输入自定义提示词 (输入 END 结束):[/yellow]")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        prompt_template = "\n".join(lines)

    if not prompt_template:
        console.print("[red]提示词为空，无法分析[/red]")
        return []

    # 获取大模型实例
    try:
        llm_provider = get_llm_provider()
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        return []

    console.print(f"\n[bold]开始分析 {len(text_files)} 个文本文件[/bold]")
    console.print(f"[blue]使用模板: {template_info['name']}[/blue]")

    result_files = []
    total = len(text_files)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("大模型分析", total=total)

        for i, text_path in enumerate(text_files, 1):
            progress.update(task, description=f"[{i}/{total}] {Path(text_path).name[:30]}")

            success = await analyze_single(llm_provider, text_path, prompt_template, template_info["name"])
            if success:
                text_path_obj = Path(text_path)
                dirs = init_data_dirs()
                result_files.append(str(dirs["analysis"] / f"{text_path_obj.stem}_分析结果.json"))
                result_files.append(str(dirs["analysis"] / f"{text_path_obj.stem}_分析报告.md"))

            progress.advance(task)

    console.print(f"\n[bold green]分析完成: 成功处理 {len(result_files)//2}/{total} 个文件[/bold green]")
    return result_files
