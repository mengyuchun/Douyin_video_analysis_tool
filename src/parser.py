"""链接解析模块 - 解析抖音分享链接，提取视频ID"""
import asyncio
import re

import httpx
from rich.console import Console

from src.config import DEFAULT_HEADERS

console = Console()

# 匹配抖音短链接 v.douyin.com
SHORT_LINK_PATTERN = re.compile(r'https?://v\.douyin\.com/[\w]+/?')

# 匹配抖音标准视频链接
STANDARD_LINK_PATTERN = re.compile(r'https?://www\.douyin\.com/video/(\d+)')

# 匹配抖音发现页链接(带modal_id)
MODAL_LINK_PATTERN = re.compile(r'modal_id=(\d+)')

# 匹配抖音笔记链接
NOTE_LINK_PATTERN = re.compile(r'https?://www\.douyin\.com/note/(\d+)')


def extract_urls(text: str) -> list[str]:
    """从文本中提取所有可能的抖音链接

    Args:
        text: 用户输入的文本，可能是分享口令或直接链接

    Returns:
        提取到的URL列表
    """
    urls = []

    # 提取 v.douyin.com 短链接
    short_links = SHORT_LINK_PATTERN.findall(text)
    urls.extend(short_links)

    # 提取标准链接
    standard_links = STANDARD_LINK_PATTERN.findall(text)
    for vid in standard_links:
        urls.append(f"https://www.douyin.com/video/{vid}")

    # 提取笔记链接
    note_links = NOTE_LINK_PATTERN.findall(text)
    for nid in note_links:
        urls.append(f"https://www.douyin.com/note/{nid}")

    # 提取modal_id链接
    existing_ids = {u.split('/')[-1] for u in urls}
    modal_ids = MODAL_LINK_PATTERN.findall(text)
    for mid in modal_ids:
        if mid not in existing_ids:
            urls.append(f"https://www.douyin.com/video/{mid}")

    return list(set(urls))


def extract_video_id(url: str) -> str | None:
    """从URL中提取视频ID

    Args:
        url: 抖音视频URL

    Returns:
        视频ID，提取失败返回None
    """
    # 标准链接 /video/ID
    match = STANDARD_LINK_PATTERN.search(url)
    if match:
        return match.group(1)

    # 笔记链接 /note/ID
    match = NOTE_LINK_PATTERN.search(url)
    if match:
        return match.group(1)

    # modal_id参数
    match = MODAL_LINK_PATTERN.search(url)
    if match:
        return match.group(1)

    return None


async def resolve_short_url(short_url: str) -> str | None:
    """解析短链接，获取重定向后的真实URL

    Args:
        short_url: v.douyin.com 短链接

    Returns:
        重定向后的完整URL，失败返回None
    """
    try:
        async with httpx.AsyncClient(follow_redirects=False) as client:
            resp = await client.get(
                short_url,
                headers={"User-Agent": DEFAULT_HEADERS["User-Agent"]},
                timeout=10,
            )

            # 从重定向Location头获取真实URL
            if resp.status_code in (301, 302, 303, 307, 308):
                location = resp.headers.get("location", "")
                if location:
                    return location

            # 有些短链接直接返回200但页面中有重定向
            if resp.status_code == 200:
                # 尝试从页面内容中提取
                text = resp.text
                match = STANDARD_LINK_PATTERN.search(text)
                if match:
                    return f"https://www.douyin.com/video/{match.group(1)}"

            console.print(f"[yellow]短链接解析失败，状态码: {resp.status_code}[/yellow]")
            return None

    except Exception as e:
        console.print(f"[red]解析短链接出错: {e}[/red]")
        return None


async def parse_douyin_link(input_text: str) -> list[dict]:
    """解析用户输入的抖音链接，短链接并发解析"""
    results = []
    urls = extract_urls(input_text)

    if not urls:
        console.print("[yellow]未在输入中找到抖音链接[/yellow]")
        return results

    # 分离短链接和标准链接
    short_urls = [u for u in urls if "v.douyin.com" in u]
    standard_urls = [u for u in urls if "v.douyin.com" not in u]

    # 标准链接直接提取ID
    for url in standard_urls:
        video_id = extract_video_id(url)
        if video_id:
            results.append({"url": url, "video_id": video_id})
            console.print(f"[green]解析成功: ID={video_id}[/green]")
        else:
            console.print(f"[yellow]无法从URL提取视频ID: {url}[/yellow]")

    # 短链接并发解析
    if short_urls:
        console.print(f"[blue]正在并发解析 {len(short_urls)} 个短链接...[/blue]")
        resolved = await asyncio.gather(*[resolve_short_url(u) for u in short_urls])
        for url, real_url in zip(short_urls, resolved):
            if real_url:
                video_id = extract_video_id(real_url)
                if video_id:
                    results.append({"url": real_url, "video_id": video_id})
                    console.print(f"[green]解析成功: ID={video_id}[/green]")
                else:
                    console.print(f"[yellow]无法从重定向URL提取视频ID: {real_url}[/yellow]")
            else:
                console.print(f"[red]短链接解析失败: {url}[/red]")

    return results


async def batch_parse_links(inputs: list[str]) -> list[dict]:
    """批量解析多条抖音链接

    Args:
        inputs: 用户输入的多条文本，每条可能包含一个或多个链接

    Returns:
        所有解析结果的列表
    """
    all_results = []
    for text in inputs:
        results = await parse_douyin_link(text.strip())
        all_results.extend(results)

    # 去重
    seen_ids = set()
    unique_results = []
    for r in all_results:
        if r["video_id"] not in seen_ids:
            seen_ids.add(r["video_id"])
            unique_results.append(r)

    console.print(f"\n[bold]共解析到 {len(unique_results)} 个不重复视频[/bold]")
    return unique_results
