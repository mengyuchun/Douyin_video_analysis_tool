"""视频转音频模块 - 从视频中提取音频"""
import asyncio
from pathlib import Path

from moviepy import VideoFileClip
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from src.config import init_data_dirs

console = Console()


def extract_audio(video_path: str, output_path: str = None, audio_format: str = "mp3") -> str | None:
    """从视频文件中提取音频"""
    video_path = Path(video_path)
    if output_path is None:
        dirs = init_data_dirs()
        output_path = dirs["audio"] / f"{video_path.stem}.{audio_format}"
    output_path = Path(output_path)

    try:
        console.print(f"[blue]正在提取音频: {video_path.name}[/blue]")
        video = VideoFileClip(str(video_path))
        try:
            audio = video.audio
            if audio is None:
                console.print(f"[yellow]视频无音频轨: {video_path.name}[/yellow]")
                return None
            try:
                audio.write_audiofile(str(output_path), logger=None)
            finally:
                audio.close()
        finally:
            video.close()

        console.print(f"[green]音频提取成功: {output_path.name}[/green]")
        return str(output_path)

    except Exception as e:
        console.print(f"[red]音频提取失败: {e}[/red]")
        return None


async def batch_extract_audio(video_paths: list[str], audio_format: str = "mp3") -> list[str]:
    """批量从视频中提取音频

    Args:
        video_paths: 视频文件路径列表
        audio_format: 输出格式 (mp3/wav/aac)

    Returns:
        成功提取的音频文件路径列表
    """
    if not video_paths:
        console.print("[yellow]没有视频文件需要处理[/yellow]")
        return []

    console.print(f"\n[bold]开始从 {len(video_paths)} 个视频中提取音频[/bold]")

    audio_files = []
    total = len(video_paths)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("提取音频", total=total)

        for i, video_path in enumerate(video_paths, 1):
            progress.update(task, description=f"[{i}/{total}] {Path(video_path).name[:30]}")

            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                extract_audio,
                video_path,
                None,
                audio_format,
            )

            if result:
                audio_files.append(result)

            progress.advance(task)

    console.print(f"\n[bold green]音频提取完成: 成功 {len(audio_files)}/{total}[/bold green]")
    return audio_files


def get_audio_info(audio_path: str) -> dict | None:
    """获取音频文件信息"""
    audio_path = Path(audio_path)
    try:
        from moviepy import AudioFileClip
        audio = AudioFileClip(str(audio_path))
        try:
            info = {
                "path": str(audio_path),
                "filename": audio_path.name,
                "duration": round(audio.duration, 2),
                "size_mb": round(audio_path.stat().st_size / (1024 * 1024), 2),
                "format": audio_path.suffix[1:],
            }
        finally:
            audio.close()
        return info
    except Exception as e:
        console.print(f"[red]获取音频信息失败: {e}[/red]")
        return None
