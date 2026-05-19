"""配置管理模块 - Cookie获取与项目配置"""
import json
import os
from pathlib import Path

import browser_cookie3
from rich.console import Console

console = Console()

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = BASE_DIR / "config.json"

# 配置缓存，避免重复读取磁盘
_config_cache: dict | None = None

# 抖音请求Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.douyin.com/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# 抖音API相关URL
DOUYIN_URLS = {
    "detail": "https://www.douyin.com/aweme/v1/web/aweme/detail/",
    "video": "https://www.douyin.com/video/",
}


def get_cookies_from_browser(browser: str = "chrome") -> dict:
    """从浏览器自动读取抖音Cookie

    Args:
        browser: 浏览器类型，支持 chrome/edge/firefox

    Returns:
        Cookie字典 {name: value}
    """
    cookie_funcs = {
        "chrome": browser_cookie3.chrome,
        "edge": browser_cookie3.edge,
        "firefox": browser_cookie3.firefox,
    }

    if browser not in cookie_funcs:
        console.print(f"[red]不支持的浏览器: {browser}，可选: {', '.join(cookie_funcs.keys())}[/red]")
        return {}

    try:
        cj = cookie_funcs[browser](domain_name=".douyin.com")
        cookies = {c.name: c.value for c in cj}
        if cookies:
            console.print(f"[green]成功从 {browser} 读取到 {len(cookies)} 个Cookie[/green]")
        else:
            console.print(f"[yellow]从 {browser} 未找到抖音Cookie，请先在浏览器中登录 douyin.com[/yellow]")
        return cookies
    except Exception as e:
        console.print(f"[red]读取{browser}Cookie失败: {e}[/red]")
        return {}


def load_config() -> dict:
    """加载配置文件，不存在则创建默认配置。结果会缓存，避免重复读磁盘。"""
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    default_config = {
        "browser": "chrome",
        "data_dir": str(DATA_DIR),
        "links_file": str(BASE_DIR / "links.txt"),
        "max_concurrent": 3,
        "cookie": {},
        # 语音识别: funasr(本地) / dashscope(云端) / whisper(本地)
        "stt_provider": "funasr",
        "stt_api_key": "",
        "whisper_model": "base",
        "funasr_model_dir": "model",
        # 大模型: dashscope(阿里云百炼) / ollama(本地) / openai(兼容接口)
        "llm_provider": "dashscope",
        "llm_api_key": "",
        "llm_model": "qwen3.5-flash",
        "ollama_base_url": "http://localhost:11434/v1",
        "ollama_model": "gemma4:e4b",
        # 输出
        "output_json": True,
        "output_markdown": True,
    }

    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            for k, v in default_config.items():
                config.setdefault(k, v)
            _config_cache = config
            return config
    else:
        save_config(default_config)
        _config_cache = default_config
        return default_config


def save_config(config: dict):
    """保存配置到文件并更新缓存"""
    global _config_cache
    _config_cache = config
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_cookies() -> dict:
    """获取Cookie，优先使用配置文件中的，否则从浏览器读取"""
    config = load_config()

    # 如果配置文件中有Cookie且非空，直接使用
    if config.get("cookie"):
        console.print("[blue]使用配置文件中的Cookie[/blue]")
        return config["cookie"]

    # 否则尝试从浏览器读取
    browser = config.get("browser", "chrome")
    console.print(f"[blue]正在从 {browser} 读取Cookie...[/blue]")
    try:
        cookies = get_cookies_from_browser(browser)
    except Exception as e:
        console.print(f"[yellow]浏览器Cookie读取失败: {e}[/yellow]")
        console.print("[yellow]请运行 python import_cookie.py 手动导入Cookie[/yellow]")
        return {}

    if cookies:
        config["cookie"] = cookies
        save_config(config)

    return cookies


def reload_config() -> dict:
    """强制重新加载配置文件"""
    global _config_cache
    _config_cache = None
    return load_config()


def init_data_dirs() -> dict:
    """确保数据目录存在，返回各子目录路径"""
    config = load_config()
    data_dir = Path(config["data_dir"])
    dirs = {
        "videos": data_dir / "videos",
        "audio": data_dir / "audio",
        "transcripts": data_dir / "transcripts",
        "analysis": data_dir / "analysis",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs
