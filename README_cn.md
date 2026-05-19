# 🎬 抖音短视频批量下载与分析工具

<p align="center">
  <strong>批量下载抖音视频 → 转音频 → 语音转文本 → 大模型结构化分析，全流程自动化</strong>
</p>

<p align="center">
  <a href="https://github.com/mengyuchun/-Douyin_video_analysis_tool/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <a href="https://github.com/mengyuchun/-Douyin_video_analysis_tool/stargazers"><img src="https://img.shields.io/github/stars/mengyuchun/-Douyin_video_analysis_tool?style=social" alt="Stars"></a>
  <a href="https://github.com/mengyuchun/-Douyin_video_analysis_tool/issues"><img src="https://img.shields.io/github/issues/mengyuchun/-Douyin_video_analysis_tool" alt="Issues"></a>
  <img src="https://img.shields.io/badge/tests-134%20passed-brightgreen.svg" alt="Tests">
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_cn.md">中文</a>
</p>

---

## ✨ 功能特性

| 功能 | 说明 |
|------|------|
| 🎥 **批量下载** | 自动解析分享口令/短链接/标准链接，批量下载无水印视频 |
| 🔊 **视频转音频** | 自动提取音频轨道（mp3/wav/aac） |
| 📝 **语音转文本** | 3 种方案：FunASR 本地离线 / 阿里云 DashScope / Whisper |
| 🤖 **大模型分析** | 3 种方案：DashScope / Ollama 本地 / OpenAI 兼容接口 |
| 🚀 **一键全流程** | 下载 → 转音频 → 转文本 → 分析，全自动 |
| 🧪 **134 个测试** | 88% 覆盖率，稳定可靠 |

## 📦 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/mengyuchun/-Douyin_video_analysis_tool.git
cd Douyin_video_analysis_tool

# 2. 创建环境
conda create -n data_env python=3.10 -y
conda activate data_env

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载语音识别模型（约 2GB，可选）
python download_models.py

# 5. 配置
cp config.example.json config.json
# 编辑 config.json，填写 API Key（使用本地模型则无需）

# 6. 运行
python main.py
```

## 🎯 使用方法

将抖音链接放入 `links.txt`（每行一个），启动程序选择功能：

```
功能菜单:
  1. 一键全流程 (下载→转音频→转文本→分析)
  2. 仅下载视频
  3. 仅视频转音频
  4. 仅音频转文本
  5. 仅大模型分析
  6. 刷新Cookie
  7. 导入Cookie
  8. 设置并发数
```

<details>
<summary>📄 支持的链接格式</summary>

```
# 分享口令（从抖音APP复制）
7.57 03/26 dAT:/ 【@用户】描述 https://v.douyin.com/xxxxx/

# 短链接
https://v.douyin.com/xxxxx/

# 标准链接
https://www.douyin.com/video/7123456789012345678

# 笔记链接
https://www.douyin.com/note/7123456789012345678
```

- `#` 开头为注释，空行自动跳过
- 自动去重
- 自动从分享口令中提取有效链接
</details>

<details>
<summary>📊 输出示例（大模型分析结果）</summary>

**内容摘要模板：**
```json
{
  "title": "教你三分钟学会Python",
  "summary": "视频介绍了Python的基础语法...",
  "keywords": ["Python", "编程入门", "教程"],
  "category": "知识分享",
  "sentiment": "正面"
}
```

**视频带货分析模板：**
```json
{
  "Hook_Type": "痛点提问",
  "Hook_Reason": "原句：'你有没有想过为什么...'，通过提问引发共鸣",
  "CTA_Softness": "情绪软植入",
  "Core_Emotion": "制造焦虑",
  "Narrative_Structure": "PAS(痛点-放大-方案)"
}
```
</details>

## ⚙️ 配置说明

### 语音识别方案

| 方案 | 配置值 | 需要 API Key | 说明 |
|------|--------|-------------|------|
| FunASR | `funasr` | ❌ | **默认**，完全离线，需下载模型（约 2GB） |
| DashScope | `dashscope` | ✅ | 阿里云云端识别，需填写 `stt_api_key` |
| Whisper | `whisper` | ❌ | 需安装 `openai-whisper` |

### 大模型方案

| 方案 | 配置值 | 需要 API Key | 默认模型 |
|------|--------|-------------|----------|
| 阿里云百炼 | `dashscope` | ✅ | qwen3.5-flash |
| Ollama 本地 | `ollama` | ❌ | qwen2.5:7b |
| OpenAI 兼容 | `openai` | ✅ | gpt-3.5-turbo |

使用 Ollama 本地模型：
```bash
# 安装 Ollama: https://ollama.com
ollama pull qwen2.5:7b
# 修改 config.json: "llm_provider": "ollama"
```

### 分析模板

| 模板 | 说明 |
|------|------|
| 内容摘要 | 标题、摘要、关键词、类别、情感 |
| 带货分析 | 商品、卖点、推广方式、转化钩子 |
| 情感分析 | 情感倾向、标签、强度 |
| 视频带货分析 | Hook类型、CTA软硬度、情绪底色、叙事结构 |
| 自定义 | 用户自行输入提示词 |

## 📁 项目结构

```
├── main.py                # 主程序入口
├── config.example.json    # 配置模板
├── download_models.py     # 模型下载脚本
├── src/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── parser.py          # 链接解析（支持分享口令/短链接/标准链接）
│   ├── api.py             # 抖音 API（A-Bogus 签名）
│   ├── downloader.py      # 异步视频下载（并发控制/进度条/断点续传）
│   ├── converter.py       # 视频转音频（moviepy）
│   ├── transcriber.py     # 音频转文本（FunASR/DashScope/Whisper）
│   └── analyzer.py        # 大模型分析（DashScope/Ollama/OpenAI）
├── model/                 # FunASR 语音模型（需单独下载）
├── data/                  # 数据输出
│   ├── videos/            # 下载的视频
│   ├── audio/             # 提取的音频
│   ├── transcripts/       # 识别的文本
│   └── analysis/          # 分析结果（JSON + Markdown）
└── tests/                 # 134 个单元测试
```

## 🔧 二次开发

### 添加新的大模型

```python
# src/analyzer.py
class NewProvider:
    async def chat(self, prompt: str, content: str) -> str:
        # 调用新模型 API
        ...
```

在 `get_llm_provider()` 中添加分支，在 `config.json` 中添加配置项。

### 添加分析模板

```python
# src/analyzer.py 的 PROMPT_TEMPLATES
PROMPT_TEMPLATES["new_template"] = {
    "name": "模板名称",
    "prompt": "你的提示词..."
}
```

## 🤝 贡献

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## ⚠️ 免责声明与风险提示

### 法律声明

本工具仅供**学习研究**和**团队内部**使用，使用者须自行承担使用本工具的一切法律责任。

**严禁将本工具用于以下用途：**

- 任何商业用途（包括但不限于转售视频内容、批量搬运牟利等）
- 侵犯他人知识产权（视频版权归原作者及平台所有）
- 违反《中华人民共和国网络安全法》《数据安全法》《个人信息保护法》等法律法规
- 突破抖音平台技术保护措施（包括但不限于反爬虫、DRM 等）
- 大规模、高频次抓取，干扰抖音平台正常运行
- 传播、分发通过本工具获取的视频内容

### 平台合规风险

- 抖音平台**明确禁止**未经授权的自动化数据采集行为
- 使用本工具可能导致您的**抖音账号被封禁或限制**
- 抖音平台可能随时更新反爬策略，导致本工具**失效**
- 本工具涉及的 A-Bogus 签名算法来自逆向工程，可能违反平台服务条款

### 数据安全风险

- Cookie 等凭据存储在本地 `config.json` 中，请妥善保管，**切勿泄露**
- 本工具不上传任何用户数据到第三方服务器
- 建议在隔离环境中运行，避免在主力账号关联的设备上使用

### AI 生成内容风险

- 大模型分析结果仅供参考，**不代表客观事实**
- 请勿将 AI 分析结果作为决策的唯一依据
- AI 生成内容可能存在偏见、错误或幻觉

### 使用建议

1. 仅下载和分析您**有合法使用权**的内容
2. 控制抓取频率，避免对目标平台造成负担
3. 定期检查并遵守抖音平台最新服务条款
4. 本工具按 [MIT License](LICENSE) 发布，**不提供任何形式的担保**

## 📄 许可证

[MIT License](LICENSE) — 仅供学习和团队内部使用。

## 🙏 致谢

本项目在开发过程中参考了以下开源项目和技术，在此致谢：

| 项目 | 致谢内容 |
|------|----------|
| [JoeanAmier/TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader) | A-Bogus 签名算法实现（`abogus.py` 移植自该项目 `src/encrypt/aBogus.py`） |
| [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) | 抖音 Web API 接口设计思路参考 |
| [modelscope/FunASR](https://github.com/modelscope/FunASR) | 阿里达摩院 FunASR 语音识别模型（paraformer-v2），本项目默认的本地离线语音识别方案 |
| [DashScope](https://dashscope.aliyun.com/) | 阿里云百炼大模型服务平台，提供语音识别和大模型 API |
| [openai/whisper](https://github.com/openai/whisper) | OpenAI 开源语音识别模型，本项目可选的本地识别方案 |
| [gmssl-python](https://github.com/emmansun/gmssl) | 国密 SM3 算法库，A-Bogus 签名的底层依赖 |

---

<p align="center">
  ⭐ 如果这个项目对你有帮助，请点个 Star 支持一下！
</p>
