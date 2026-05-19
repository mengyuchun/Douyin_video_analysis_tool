"""抖音短视频批量下载工具 - 主程序"""
import asyncio
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, Confirm

from src.config import get_cookies, load_config, save_config, init_data_dirs
from src.parser import batch_parse_links
from src.api import batch_get_video_info
from src.downloader import batch_download_videos
from src.converter import batch_extract_audio

console = Console()

BANNER = """
╔══════════════════════════════════════════════════════════╗
║            抖音短视频批量下载与分析工具 v2.0              ║
║                                                          ║
║  功能: 下载视频 → 转音频 → 转文本 → 大模型结构化输出      ║
║  使用: 将链接放入 links.txt，选择功能即可                 ║
╚══════════════════════════════════════════════════════════╝
"""


def show_menu():
    """显示主菜单"""
    console.print(Panel(BANNER, style="bold cyan"))
    console.print("[bold]功能菜单:[/bold]")
    console.print("  1. 一键全流程 (下载→转音频→转文本→分析)")
    console.print("  2. 仅下载视频")
    console.print("  3. 仅视频转音频")
    console.print("  4. 仅音频转文本")
    console.print("  5. 仅大模型分析")
    console.print("  6. 刷新Cookie")
    console.print("  7. 导入Cookie (手动粘贴)")
    console.print("  8. 设置并发数")
    console.print("  0. 退出")
    console.print()


def read_links_from_file(filepath: str) -> list[str]:
    """从txt文件读取链接

    Args:
        filepath: 链接文件路径

    Returns:
        链接列表
    """
    path = Path(filepath)
    if not path.exists():
        console.print(f"[red]链接文件不存在: {path}[/red]")
        console.print("[yellow]请创建 links.txt 文件，每行放一个抖音链接[/yellow]")
        return []

    links = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith("#"):
                continue
            links.append(line)

    if not links:
        console.print("[yellow]links.txt 中没有找到有效链接[/yellow]")
    else:
        console.print(f"[green]从文件读取到 {len(links)} 个链接[/green]")

    return links


async def step_download(links: list[str]) -> list[str]:
    """步骤1: 下载视频，返回下载的文件路径列表"""
    cookies = get_cookies()
    if not cookies:
        console.print("[red]无法获取Cookie，请先在浏览器中登录 douyin.com[/red]")
        return []

    video_list = await batch_parse_links(links)
    if not video_list:
        console.print("[red]未能解析出任何有效视频链接[/red]")
        return []

    video_info_list = await batch_get_video_info(video_list, cookies)
    if not video_info_list:
        console.print("[red]未能获取到任何视频信息[/red]")
        return []

    downloaded = await batch_download_videos(video_info_list)
    return downloaded


async def step_convert_audio(video_files: list[str]) -> list[str]:
    """步骤2: 视频转音频"""
    if not video_files:
        dirs = init_data_dirs()
        video_files = [str(f) for f in dirs["videos"].glob("*.mp4")]

    if not video_files:
        console.print("[yellow]没有视频文件可处理[/yellow]")
        return []

    return await batch_extract_audio(video_files)


async def step_transcribe(audio_files: list[str]) -> list[str]:
    """步骤3: 音频转文本"""
    if not audio_files:
        dirs = init_data_dirs()
        audio_files = [str(f) for f in dirs["audio"].glob("*.mp3")]

    if not audio_files:
        console.print("[yellow]没有音频文件可处理[/yellow]")
        return []

    # 延迟导入，避免未安装时启动报错
    try:
        from src.transcriber import batch_transcribe
        return await batch_transcribe(audio_files)
    except ImportError:
        console.print("[red]语音识别模块未安装，请先创建 transcriber.py[/red]")
        return []


async def step_analyze(text_files: list[str]) -> list[str]:
    """步骤4: 大模型结构化输出"""
    if not text_files:
        dirs = init_data_dirs()
        text_files = [str(f) for f in dirs["transcripts"].glob("*.txt")]

    if not text_files:
        console.print("[yellow]没有文本文件可处理[/yellow]")
        return []

    try:
        from src.analyzer import batch_analyze
        return await batch_analyze(text_files)
    except ImportError:
        console.print("[red]大模型分析模块未安装，请先创建 analyzer.py[/red]")
        return []


async def full_pipeline():
    """一键全流程"""
    links = read_links_from_file(load_config().get("links_file", "links.txt"))
    if not links:
        return

    console.print("\n[bold cyan]═══ 开始全流程处理 ═══[/bold cyan]")
    console.print("[bold]流程: 下载视频 → 转音频 → 转文本 → 大模型分析[/bold]\n")

    # Step 1: 下载
    console.print("[bold]─── 步骤 1/4: 下载视频 ───[/bold]")
    video_files = await step_download(links)

    # Step 2: 转音频
    console.print("\n[bold]─── 步骤 2/4: 视频转音频 ───[/bold]")
    audio_files = await step_convert_audio(video_files)

    # Step 3: 转文本
    console.print("\n[bold]─── 步骤 3/4: 音频转文本 ───[/bold]")
    text_files = await step_transcribe(audio_files)

    # Step 4: 大模型分析
    console.print("\n[bold]─── 步骤 4/4: 大模型分析 ───[/bold]")
    result_files = await step_analyze(text_files)

    # 结果汇总
    console.print("\n[bold cyan]═══ 全流程完成 ═══[/bold cyan]")
    console.print(f"  下载视频: {len(video_files)} 个")
    console.print(f"  提取音频: {len(audio_files)} 个")
    console.print(f"  识别文本: {len(text_files)} 个")
    console.print(f"  分析结果: {len(result_files)} 个")


async def download_only():
    """仅下载视频"""
    links = read_links_from_file(load_config().get("links_file", "links.txt"))
    if not links:
        return
    await step_download(links)


async def convert_only():
    """仅视频转音频"""
    await step_convert_audio([])


async def transcribe_only():
    """仅音频转文本"""
    await step_transcribe([])


async def analyze_only():
    """仅大模型分析"""
    await step_analyze([])


def refresh_cookie():
    """刷新Cookie"""
    config = load_config()
    config["cookie"] = {}
    save_config(config)
    console.print("[green]Cookie已清除，下次运行时将自动从浏览器重新读取[/green]")


def set_concurrency():
    """设置并发数"""
    config = load_config()
    current = config.get("max_concurrent", 3)
    console.print(f"[blue]当前并发数: {current}[/blue]")
    new_val = IntPrompt.ask("请输入新的并发数(1-10)", default=current)
    new_val = max(1, min(10, new_val))
    config["max_concurrent"] = new_val
    save_config(config)
    console.print(f"[green]并发数已设置为: {new_val}[/green]")


def import_cookie_interactive():
    """交互式导入Cookie"""
    console.print("\n[bold]导入Cookie[/bold]")
    console.print("操作步骤:")
    console.print("  1. 用Chrome打开 https://www.douyin.com 并登录")
    console.print("  2. 按 F12 打开开发者工具 → Network 标签")
    console.print("  3. 刷新页面，点击任意请求，找到 Cookie 头")
    console.print("  4. 复制Cookie值粘贴到下方")
    console.print()
    console.print("[yellow]提示: 右键粘贴，Ctrl+V在某些终端不生效[/yellow]")
    console.print("-" * 50)

    cookie_str = input("请粘贴Cookie: ").strip()

    if not cookie_str:
        console.print("[red]Cookie为空，已取消[/red]")
        return

    cookies = {}
    for item in cookie_str.split(";"):
        item = item.strip()
        if "=" in item:
            name, value = item.split("=", 1)
            cookies[name.strip()] = value.strip()

    if len(cookies) < 3:
        console.print(f"[yellow]只解析到 {len(cookies)} 个Cookie，可能不完整[/yellow]")

    config = load_config()
    config["cookie"] = cookies
    save_config(config)
    console.print(f"[green]已保存 {len(cookies)} 个Cookie[/green]")


async def main():
    """主程序入口"""
    while True:
        show_menu()
        choice = Prompt.ask("请选择功能", choices=["0","1","2","3","4","5","6","7","8"], default="1")

        if choice == "0":
            console.print("[bold green]再见！[/bold green]")
            break
        elif choice == "1":
            await full_pipeline()
        elif choice == "2":
            await download_only()
        elif choice == "3":
            await convert_only()
        elif choice == "4":
            await transcribe_only()
        elif choice == "5":
            await analyze_only()
        elif choice == "6":
            refresh_cookie()
        elif choice == "7":
            import_cookie_interactive()
        elif choice == "8":
            set_concurrency()

        console.print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]程序已中断[/bold yellow]")
        sys.exit(0)
