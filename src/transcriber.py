"""音频转文本模块 - 语音识别，支持云端(阿里云DashScope)、本地Whisper、本地FunASR"""
import asyncio
import json
from pathlib import Path
from urllib import request as url_request

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.config import load_config, init_data_dirs

console = Console()


# ==================== 阿里云 DashScope 语音识别 ====================

class DashScopeSTT:
    """阿里云 DashScope 语音识别 (Paraformer/FunASR)"""

    def __init__(self, api_key: str):
        import dashscope
        self.api_key = api_key
        dashscope.api_key = api_key
        dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

    async def transcribe(self, audio_path: str) -> str:
        """识别本地音频文件

        Args:
            audio_path: 音频文件路径 (支持mp3/wav/m4a/aac等)

        Returns:
            识别出的文本
        """
        from dashscope.audio.asr import Transcription

        audio_path = Path(audio_path).resolve()

        # DashScope Transcription 需要文件URL，本地文件需先上传或使用file://协议
        # 这里使用同步方式处理，放到线程池中执行
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._transcribe_sync, str(audio_path))
        return result

    def _transcribe_sync(self, audio_path: str) -> str:
        """同步执行语音识别"""
        import dashscope
        from dashscope.audio.asr import Transcription

        # 对于本地文件，需要先上传到可访问的URL
        # 这里使用 file:// 协议（DashScope支持本地文件路径）
        file_url = f"file://{audio_path}"

        task_response = Transcription.async_call(
            model='paraformer-v2',
            file_urls=[file_url],
            language_hints=['zh', 'en'],
        )

        # 等待任务完成
        transcription_response = Transcription.wait(task=task_response.output.task_id)

        if transcription_response.status_code != 200:
            raise Exception(f"DashScope识别失败: {transcription_response.output.message}")

        # 提取识别结果
        texts = []
        for transcription in transcription_response.output['results']:
            if transcription['subtask_status'] == 'SUCCEEDED':
                url = transcription['transcription_url']
                result = json.loads(url_request.urlopen(url).read().decode('utf8'))
                # 提取transcription_text
                if 'transcription' in result:
                    for item in result['transcription']:
                        if 'text' in item:
                            texts.append(item['text'])
            else:
                console.print(f"[yellow]部分音频识别失败: {transcription.get('subtask_status')}[/yellow]")

        return "\n".join(texts)


# ==================== 本地 Whisper ====================

class LocalWhisper:
    """本地 Whisper 语音识别"""

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def _load_model(self):
        """延迟加载模型"""
        if self._model is None:
            try:
                import whisper
                console.print(f"[blue]正在加载 Whisper {self.model_name} 模型...[/blue]")
                self._model = whisper.load_model(self.model_name)
                console.print("[green]Whisper 模型加载完成[/green]")
            except ImportError:
                raise Exception("未安装 whisper，请运行: pip install openai-whisper")

    async def transcribe(self, audio_path: str) -> str:
        """识别音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            识别出的文本
        """
        self._load_model()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._model.transcribe(audio_path, language="zh"),
        )

        return result.get("text", "")


# ==================== 本地 FunASR ====================

class FunASRLocal:
    """本地 FunASR 语音识别（Paraformer + VAD + 标点恢复）"""

    ASR_DIR = "speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
    VAD_DIR = "speech_fsmn_vad_zh-cn-16k-common-pytorch"
    PUNC_DIR = "punc_ct-transformer_cn-en-common-vocab471067-large"

    def __init__(self, model_dir: str = "model"):
        self.model_dir = Path(__file__).parent.parent / model_dir
        self._pipeline = None

    def _load_pipeline(self):
        """延迟加载 FunASR Pipeline"""
        if self._pipeline is None:
            try:
                from funasr import AutoModel
            except ImportError:
                raise Exception("未安装 funasr，请运行: pip install funasr")

            console.print("[blue]正在加载 FunASR 本地模型...[/blue]")
            self._pipeline = AutoModel(
                model=str(self.model_dir / self.ASR_DIR),
                vad_model=str(self.model_dir / self.VAD_DIR),
                punc_model=str(self.model_dir / self.PUNC_DIR),
            )
            console.print("[green]FunASR 模型加载完成[/green]")

    async def transcribe(self, audio_path: str) -> str:
        """识别音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            识别出的带标点文本
        """
        self._load_pipeline()

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._transcribe_sync, audio_path)
        return result

    def _transcribe_sync(self, audio_path: str) -> str:
        """同步执行语音识别"""
        result = self._pipeline.generate(input=audio_path)
        if result and len(result) > 0:
            return result[0].get("text", "")
        return ""


# ==================== 统一接口 ====================

def get_transcriber():
    """根据配置返回对应的转写器实例"""
    config = load_config()
    provider = config.get("stt_provider", "funasr")

    if provider == "dashscope":
        api_key = config.get("stt_api_key", "") or config.get("dashscope_api_key", "")
        if not api_key:
            raise Exception("请在config.json中配置 stt_api_key (阿里云DashScope API Key)")
        return DashScopeSTT(api_key)

    elif provider == "whisper":
        model_name = config.get("whisper_model", "base")
        return LocalWhisper(model_name)

    elif provider == "funasr":
        model_dir = config.get("funasr_model_dir", "model")
        return FunASRLocal(model_dir)

    else:
        raise Exception(f"不支持的语音识别提供商: {provider}，可选: funasr / dashscope / whisper")


def save_transcript(text: str, audio_path: str) -> str:
    """保存转写结果到 data/transcripts/

    Args:
        text: 识别出的文本
        audio_path: 原始音频文件路径

    Returns:
        保存的文件路径
    """
    audio_path = Path(audio_path)
    dirs = init_data_dirs()
    output_path = dirs["transcripts"] / f"{audio_path.stem}.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    return str(output_path)


async def transcribe_single(transcriber, audio_path: str) -> str | None:
    """识别单个音频文件并保存"""
    try:
        console.print(f"[blue]正在识别: {Path(audio_path).name}[/blue]")
        text = await transcriber.transcribe(audio_path)

        if text and text.strip():
            output_path = save_transcript(text, audio_path)
            console.print(f"[green]识别完成: {Path(audio_path).name} → {Path(output_path).name}[/green]")
            return output_path
        else:
            console.print(f"[yellow]识别结果为空: {Path(audio_path).name}[/yellow]")
            return None

    except Exception as e:
        console.print(f"[red]识别失败 {Path(audio_path).name}: {e}[/red]")
        return None


async def batch_transcribe(audio_files: list[str]) -> list[str]:
    """批量语音识别

    Args:
        audio_files: 音频文件路径列表

    Returns:
        生成的文本文件路径列表
    """
    if not audio_files:
        console.print("[yellow]没有音频文件需要识别[/yellow]")
        return []

    try:
        transcriber = get_transcriber()
    except Exception as e:
        console.print(f"[red]{e}[/red]")
        return []

    console.print(f"\n[bold]开始识别 {len(audio_files)} 个音频文件[/bold]")

    text_files = []
    total = len(audio_files)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("语音识别", total=total)

        for i, audio_path in enumerate(audio_files, 1):
            progress.update(task, description=f"[{i}/{total}] {Path(audio_path).name[:30]}")

            result = await transcribe_single(transcriber, audio_path)
            if result:
                text_files.append(result)

            progress.advance(task)

    console.print(f"\n[bold green]语音识别完成: 成功 {len(text_files)}/{total}[/bold green]")
    return text_files
