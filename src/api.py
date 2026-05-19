"""抖音API封装模块 - 获取视频元数据和下载地址"""
import asyncio
import json
import re

import httpx
from rich.console import Console

from src.abogus import ABogus
from src.config import DEFAULT_HEADERS, DOUYIN_URLS, load_config

console = Console()

DETAIL_API = DOUYIN_URLS["detail"]
IESDOUYIN_API = "https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/"
VIDEO_PAGE_URL = DOUYIN_URLS["video"]

# A-Bogus 签名实例（复用）
_abogus = None


def _get_abogus() -> ABogus:
    global _abogus
    if _abogus is None:
        _abogus = ABogus()
    return _abogus


def clean_title(title: str) -> str:
    """清理视频标题，移除不合法的文件名字符"""
    title = re.sub(r'[\\/:*?"<>|\n\r]', '', title)
    title = title.strip()[:80]  # 限制长度
    return title if title else "untitled"


async def get_video_info(video_id: str, cookies: dict, client: httpx.AsyncClient = None) -> dict | None:
    """获取视频详情，三种方式依次尝试"""
    # 方式1: 带 A-Bogus 签名的官方 API
    result = await _get_from_signed_api(video_id, cookies, client)
    if result:
        return result

    # 方式2: iesdouyin API (反爬较宽松)
    result = await _get_from_iesdouyin(video_id, client)
    if result:
        return result

    # 方式3: 从网页HTML解析
    result = await _get_from_page(video_id, cookies, client)
    if result:
        return result

    console.print(f"[red]无法获取视频信息: {video_id}[/red]")
    return None


async def _get_from_signed_api(video_id: str, cookies: dict, client: httpx.AsyncClient = None) -> dict | None:
    """通过带 A-Bogus 签名的官方 API 获取视频信息"""
    params = {
        "aweme_id": video_id,
        "aid": "6383",
        "channel": "channel_pc_web",
        "version_code": "190500",
        "version_name": "19.5.0",
        "device_platform": "webapp",
        "cookie_enabled": "true",
        "browser_name": "Chrome",
        "browser_version": "120.0.0.0",
        "os_name": "Windows",
        "os_version": "10",
        "cpu_core_num": "16",
        "device_memory": "8",
        "platform": "PC",
        "downlink": "10",
    }

    # 生成 A-Bogus 签名
    ab = _get_abogus()
    import urllib.parse
    qs = urllib.parse.urlencode(params)
    a_bogus = ab.get_value(qs, "GET")
    params["a_bogus"] = a_bogus

    headers = {
        **DEFAULT_HEADERS,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        async def _do(c):
            return await c.get(DETAIL_API, params=params, headers=headers, cookies=cookies, timeout=15)

        if client:
            resp = await _do(client)
        else:
            async with httpx.AsyncClient(follow_redirects=True) as c:
                resp = await _do(c)

        if resp.status_code != 200 or not resp.text.strip():
            return None

        data = resp.json()
        if data.get("status_code") != 0:
            return None

        detail = data.get("aweme_detail")
        if not detail:
            return None

        video = detail.get("video", {})
        author = detail.get("author", {})
        desc = detail.get("desc", "无标题")

        play_addr = video.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        download_url = url_list[0] if url_list else None

        if not download_url:
            bit_rate = video.get("bit_rate", [])
            if bit_rate:
                best = max(bit_rate, key=lambda x: x.get("bit_rate", 0))
                url_list = best.get("play_addr", {}).get("url_list", [])
                if url_list:
                    download_url = url_list[0]

        if not download_url:
            return None

        download_url = download_url.replace("playwm", "play")
        if not download_url.startswith("http"):
            download_url = "https:" + download_url

        cover = video.get("cover", {})
        cover_urls = cover.get("url_list", [])
        cover_url = cover_urls[0] if cover_urls else None

        result = {
            "video_id": video_id,
            "desc": clean_title(desc),
            "author": author.get("nickname", "未知作者"),
            "download_url": download_url,
            "cover_url": cover_url,
            "duration": video.get("duration", 0),
        }
        console.print(f"[green]API签名获取成功: {result['author']} - {result['desc'][:30]}[/green]")
        return result

    except Exception:
        return None


async def _get_from_iesdouyin(video_id: str, client: httpx.AsyncClient = None) -> dict | None:
    """通过 iesdouyin API 获取视频信息"""
    params = {"item_ids": video_id}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.douyin.com/",
        "Accept": "application/json",
    }

    try:
        async def _do_request(c):
            return await c.get(IESDOUYIN_API, params=params, headers=headers, timeout=15)

        if client:
            resp = await _do_request(client)
        else:
            async with httpx.AsyncClient(follow_redirects=True) as c:
                resp = await _do_request(c)

        if resp.status_code != 200:
            return None

        if not resp.text.strip():
            return None

        data = resp.json()

        item_list = data.get("item_list", [])
        if not item_list:
            return None

        item = item_list[0]
        video = item.get("video", {})
        author = item.get("author", {})

        # 获取下载地址
        play_addr = video.get("play_addr", {})
        url_list = play_addr.get("url_list", [])
        download_url = url_list[0] if url_list else None

        if not download_url:
            # 尝试 bit_rate
            bit_rate = video.get("bit_rate", [])
            if bit_rate:
                best = max(bit_rate, key=lambda x: x.get("bit_rate", 0))
                url_list = best.get("play_addr", {}).get("url_list", [])
                if url_list:
                    download_url = url_list[0]

        if not download_url:
            return None

        # 替换为无水印地址
        download_url = download_url.replace("playwm", "play")
        if not download_url.startswith("http"):
            download_url = "https:" + download_url

        # 尝试用 play_addr_h264 或 play_addr_265
        h264 = video.get("play_addr_h264", {})
        h264_urls = h264.get("url_list", [])
        if h264_urls:
            download_url = h264_urls[0].replace("playwm", "play")
            if not download_url.startswith("http"):
                download_url = "https:" + download_url

        cover = video.get("cover", {})
        cover_urls = cover.get("url_list", [])
        cover_url = cover_urls[0] if cover_urls else None

        result = {
            "video_id": video_id,
            "desc": clean_title(item.get("desc", "无标题")),
            "author": author.get("nickname", "未知作者"),
            "download_url": download_url,
            "cover_url": cover_url,
            "duration": video.get("duration", 0),
        }

        console.print(f"[green]获取视频信息成功: {result['author']} - {result['desc'][:30]}[/green]")
        return result

    except Exception:
        return None


async def _get_from_page(video_id: str, cookies: dict, client: httpx.AsyncClient = None) -> dict | None:
    """从视频页面解析信息（备用方案）"""
    url = f"{VIDEO_PAGE_URL}{video_id}"
    headers = {
        **DEFAULT_HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    try:
        async def _do_request(c):
            return await c.get(url, headers=headers, cookies=cookies, timeout=20)

        if client:
            resp = await _do_request(client)
        else:
            async with httpx.AsyncClient(follow_redirects=True) as c:
                resp = await _do_request(c)

        if resp.status_code != 200:
            return None

        html = resp.text

        # 从 RENDER_DATA 中提取
        render_match = re.search(r'<script\s+id="RENDER_DATA"\s+type="application/json">([^<]+)</script>', html)
        if render_match:
            from urllib.parse import unquote
            raw = unquote(render_match.group(1))
            data = json.loads(raw)
            result = _extract_from_render_data(data, video_id)
            if result:
                console.print(f"[green]从页面解析成功: {result['author']} - {result['desc'][:30]}[/green]")
                return result

        # 正则提取
        video_url_match = re.search(r'"playApi"\s*:\s*"([^"]+)"', html)
        desc_match = re.search(r'"desc"\s*:\s*"([^"]*)"', html)
        author_match = re.search(r'"nickname"\s*:\s*"([^"]*)"', html)

        if video_url_match:
            download_url = video_url_match.group(1).replace("\\u002F", "/")
            if not download_url.startswith("http"):
                download_url = "https:" + download_url

            return {
                "video_id": video_id,
                "desc": clean_title(desc_match.group(1)) if desc_match else "无标题",
                "author": author_match.group(1) if author_match else "未知作者",
                "download_url": download_url.replace("playwm", "play"),
                "cover_url": None,
                "duration": 0,
            }

        return None

    except Exception:
        return None


def _extract_from_render_data(data: dict, video_id: str) -> dict | None:
    """从RENDER_DATA中提取视频信息"""
    # 递归查找 aweme_detail 或类似结构
    detail = _find_aweme_detail(data)
    if not detail:
        return None

    video = detail.get("video", {})
    author = detail.get("author", {})
    desc = detail.get("desc", "无标题")

    play_addr = video.get("play_addr", {})
    url_list = play_addr.get("url_list", [])
    download_url = url_list[0] if url_list else None

    if not download_url:
        bit_rate = video.get("bit_rate", [])
        if bit_rate:
            best = max(bit_rate, key=lambda x: x.get("bit_rate", 0))
            url_list = best.get("play_addr", {}).get("url_list", [])
            if url_list:
                download_url = url_list[0]

    if not download_url:
        return None

    download_url = download_url.replace("playwm", "play")
    if not download_url.startswith("http"):
        download_url = "https:" + download_url

    cover = video.get("cover", {})
    cover_urls = cover.get("url_list", [])
    cover_url = cover_urls[0] if cover_urls else None

    return {
        "video_id": video_id,
        "desc": clean_title(desc),
        "author": author.get("nickname", "未知作者"),
        "download_url": download_url,
        "cover_url": cover_url,
        "duration": video.get("duration", 0),
    }


def _find_aweme_detail(data) -> dict | None:
    """递归查找aweme_detail"""
    if isinstance(data, dict):
        if "aweme_detail" in data:
            return data["aweme_detail"]
        if "awemeDetail" in data:
            return data["awemeDetail"]
        for v in data.values():
            result = _find_aweme_detail(v)
            if result:
                return result
    elif isinstance(data, list):
        for item in data:
            result = _find_aweme_detail(item)
            if result:
                return result
    return None


async def batch_get_video_info(video_list: list[dict], cookies: dict) -> list[dict]:
    """并发批量获取视频信息"""
    config = load_config()
    max_concurrent = config.get("max_concurrent", 3)
    sem = asyncio.Semaphore(max_concurrent)
    total = len(video_list)

    console.print(f"\n[bold]正在并发获取 {total} 个视频信息 (并发数={max_concurrent})...[/bold]")

    async with httpx.AsyncClient(follow_redirects=True) as client:
        async def _fetch(i, item):
            async with sem:
                console.print(f"[blue]获取第 {i}/{total} 个: {item['video_id']}[/blue]")
                return await get_video_info(item["video_id"], cookies, client=client)

        tasks = [_fetch(i, item) for i, item in enumerate(video_list, 1)]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    results = []
    for item, r in zip(video_list, raw_results):
        if isinstance(r, Exception):
            console.print(f"[red]获取失败 {item['video_id']}: {r}[/red]")
        elif r:
            results.append(r)
        else:
            console.print(f"[yellow]跳过视频: {item['video_id']}[/yellow]")

    console.print(f"\n[bold]成功获取 {len(results)}/{total} 个视频信息[/bold]")
    return results
