"""异步视频下载器 - 批量下载抖音视频"""
import asyncio
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn

from src.config import DEFAULT_HEADERS, init_data_dirs, load_config

console = Console()


def generate_filename(video_info: dict) -> str:
    """生成视频文件名

    格式: {作者}_{标题}_{ID}.mp4
    """
    author = video_info.get("author", "未知作者")
    desc = video_info.get("desc", "untitled")
    video_id = video_info.get("video_id", "unknown")

    # 清理文件名
    for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']:
        author = author.replace(char, '')
        desc = desc.replace(char, '')

    author = author.strip()[:30]
    desc = desc.strip()[:50]

    if not author:
        author = "未知作者"
    if not desc:
        desc = "无标题"

    return f"{author}_{desc}_{video_id}.mp4"


def desc_short(video_info: dict) -> str:
    """生成简短描述用于进度条显示"""
    author = video_info.get("author", "")[:10]
    desc = video_info.get("desc", "")[:15]
    return f"{author}_{desc}"


class AsyncStreamContextManager:
    """异步流式响应上下文管理器"""
    def __init__(self, client, method, url, **kwargs):
        self._client = client
        self._method = method
        self._url = url
        self._kwargs = kwargs
        self._response = None

    async def __aenter__(self):
        self._response = await self._client.send(
            self._client.build_request(self._method, self._url, **self._kwargs),
            stream=True,
        )
        return self._response

    async def __aexit__(self, *args):
        if self._response:
            await self._response.aclose()


async def download_single_video(
    client: httpx.AsyncClient,
    video_info: dict,
    download_dir: Path,
    semaphore: asyncio.Semaphore,
    progress: Progress,
) -> str | None:
    """下载单个视频

    Returns:
        下载成功返回文件路径
    """
    filename = generate_filename(video_info)
    filepath = download_dir / filename
    video_id = video_info.get("video_id", "unknown")
    download_url = video_info.get("download_url")

    if not download_url:
        console.print(f"[red]视频 {video_id} 无下载地址[/red]")
        return None

    if filepath.exists():
        console.print(f"[yellow]文件已存在，跳过: {filename}[/yellow]")
        return str(filepath)

    temp_path = filepath.with_suffix(".tmp")
    task_id = None
    async with semaphore:
        try:
            task_id = progress.add_task(f"下载 {desc_short(video_info)}", total=None)

            async with AsyncStreamContextManager(
                client, "GET", download_url,
                headers={**DEFAULT_HEADERS},
                timeout=60,
            ) as resp:
                if resp.status_code != 200:
                    console.print(f"[red]下载失败 {video_id}: HTTP {resp.status_code}[/red]")
                    return None

                total = int(resp.headers.get("content-length", 0))
                if total:
                    progress.update(task_id, total=total)

                downloaded = 0
                with open(temp_path, "wb") as f:
                    async for chunk in resp.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            progress.update(task_id, completed=downloaded)

            temp_path.rename(filepath)
            console.print(f"[green]下载完成: {filename}[/green]")
            return str(filepath)

        except (httpx.TimeoutException, Exception) as e:
            console.print(f"[red]下载失败 {video_id}: {e}[/red]")
            return None
        finally:
            if task_id is not None:
                progress.remove_task(task_id)
            if temp_path.exists():
                temp_path.unlink()


async def batch_download_videos(video_list: list[dict]) -> list[str]:
    """批量下载视频

    Args:
        video_list: 视频信息列表

    Returns:
        成功下载的文件路径列表
    """
    if not video_list:
        console.print("[yellow]没有视频需要下载[/yellow]")
        return []

    config = load_config()
    dirs = init_data_dirs()
    download_dir = dirs["videos"]
    max_concurrent = config.get("max_concurrent", 3)

    console.print(f"\n[bold]开始下载 {len(video_list)} 个视频到: {download_dir}[/bold]")
    console.print(f"[blue]最大并发数: {max_concurrent}[/blue]\n")

    semaphore = asyncio.Semaphore(max_concurrent)
    downloaded_files = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console,
    ) as progress:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            tasks = [
                download_single_video(client, info, download_dir, semaphore, progress)
                for info in video_list
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, str) and result:
                    downloaded_files.append(result)

    success_count = len(downloaded_files)
    console.print(f"\n[bold green]下载完成: 成功 {success_count}/{len(video_list)}[/bold green]")
    return downloaded_files
