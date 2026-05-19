"""共享测试夹具"""
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def tmp_dir(tmp_path):
    """提供临时目录"""
    return tmp_path


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "browser": "chrome",
        "data_dir": "/tmp/data",
        "links_file": "/tmp/links.txt",
        "max_concurrent": 3,
        "cookie": {"sessionid": "test123"},
        "stt_provider": "funasr",
        "stt_api_key": "",
        "whisper_model": "base",
        "funasr_model_dir": "model",
        "llm_provider": "dashscope",
        "llm_api_key": "test_llm_key",
        "llm_model": "qwen3.5-flash",
        "ollama_base_url": "http://localhost:11434/v1",
        "ollama_model": "qwen2.5:7b",
        "output_json": True,
        "output_markdown": True,
    }


@pytest.fixture
def sample_video_info():
    """示例视频信息"""
    return {
        "video_id": "1234567890",
        "desc": "测试视频标题",
        "author": "测试作者",
        "download_url": "https://example.com/video.mp4",
        "cover_url": "https://example.com/cover.jpg",
        "duration": 15000,
    }


@pytest.fixture
def sample_links_file(tmp_path):
    """创建示例链接文件"""
    links_file = tmp_path / "links.txt"
    links_file.write_text(
        "https://www.douyin.com/video/123456\n"
        "# 这是注释\n"
        "https://v.douyin.com/abc123/\n"
        "\n"
        "https://www.douyin.com/video/789012\n",
        encoding="utf-8",
    )
    return str(links_file)


@pytest.fixture
def mock_config(tmp_path, sample_config):
    """模拟配置模块，使用临时目录"""
    config_file = tmp_path / "src.config.json"
    config_file.write_text(json.dumps(sample_config, ensure_ascii=False), encoding="utf-8")

    with patch("src.config.CONFIG_FILE", config_file), \
         patch("src.config.DATA_DIR", tmp_path / "data"), \
         patch("src.config.BASE_DIR", tmp_path), \
         patch("src.config._config_cache", None):
        yield sample_config
