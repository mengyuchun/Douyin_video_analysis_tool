"""src.config.py 测试"""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.config import (
    get_cookies,
    get_cookies_from_browser,
    init_data_dirs,
    load_config,
    reload_config,
    save_config,
)


class TestLoadConfig:
    """load_config 测试"""

    def test_load_default_config_when_file_missing(self, tmp_path):
        """配置文件不存在时创建默认配置"""
        config_file = tmp_path / "config.json"
        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config.DATA_DIR", tmp_path / "downloads"), \
             patch("src.config.BASE_DIR", tmp_path), \
             patch("src.config._config_cache", None):
            config = load_config()

            assert config["browser"] == "chrome"
            assert config["max_concurrent"] == 3
            assert config["stt_provider"] == "funasr"
            assert config["llm_provider"] == "dashscope"
            assert config_file.exists()

    def test_load_existing_config(self, tmp_path, sample_config):
        """加载已有配置文件"""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(sample_config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None):
            config = load_config()

            assert config["browser"] == "chrome"
            assert config["cookie"] == {"sessionid": "test123"}

    def test_load_config_with_missing_keys_fills_defaults(self, tmp_path):
        """配置文件缺少某些键时自动填充默认值"""
        config_file = tmp_path / "config.json"
        partial = {"browser": "edge", "max_concurrent": 5}
        config_file.write_text(json.dumps(partial), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config.DATA_DIR", tmp_path / "downloads"), \
             patch("src.config.BASE_DIR", tmp_path), \
             patch("src.config._config_cache", None):
            config = load_config()

            assert config["browser"] == "edge"
            assert config["max_concurrent"] == 5
            assert config["stt_provider"] == "funasr"

    def test_load_config_uses_cache(self, tmp_path, sample_config):
        """配置缓存生效"""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(sample_config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", sample_config):
            config = load_config()
            assert config == sample_config


class TestSaveConfig:
    """save_config 测试"""

    def test_save_config_writes_file(self, tmp_path):
        """保存配置写入文件"""
        config_file = tmp_path / "config.json"
        config = {"browser": "firefox", "max_concurrent": 5}

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None):
            save_config(config)

            assert config_file.exists()
            saved = json.loads(config_file.read_text(encoding="utf-8"))
            assert saved["browser"] == "firefox"

    def test_save_config_updates_cache(self, tmp_path):
        """保存配置更新缓存"""
        config_file = tmp_path / "config.json"
        config = {"browser": "edge"}

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None):
            import src.config as config_mod
            save_config(config)
            assert config_mod._config_cache == config


class TestGetCookiesFromBrowser:
    """get_cookies_from_browser 测试"""

    def test_unsupported_browser_returns_empty(self):
        """不支持的浏览器返回空字典"""
        result = get_cookies_from_browser("safari")
        assert result == {}

    @patch("src.config.browser_cookie3")
    def test_chrome_cookies_success(self, mock_bc):
        """成功从Chrome读取Cookie"""
        mock_cookie = MagicMock()
        mock_cookie.name = "sessionid"
        mock_cookie.value = "abc123"
        mock_bc.chrome.return_value = [mock_cookie]

        result = get_cookies_from_browser("chrome")
        assert result == {"sessionid": "abc123"}

    @patch("src.config.browser_cookie3")
    def test_chrome_cookies_empty(self, mock_bc):
        """Chrome无Cookie时返回空"""
        mock_bc.chrome.return_value = []

        result = get_cookies_from_browser("chrome")
        assert result == {}

    @patch("src.config.browser_cookie3")
    def test_chrome_cookies_exception(self, mock_bc):
        """读取Cookie异常时返回空"""
        mock_bc.chrome.side_effect = Exception("access denied")

        result = get_cookies_from_browser("chrome")
        assert result == {}

    @patch("src.config.browser_cookie3")
    def test_edge_cookies(self, mock_bc):
        """从Edge读取Cookie"""
        mock_cookie = MagicMock()
        mock_cookie.name = "token"
        mock_cookie.value = "xyz"
        mock_bc.edge.return_value = [mock_cookie]

        result = get_cookies_from_browser("edge")
        assert result == {"token": "xyz"}

    @patch("src.config.browser_cookie3")
    def test_firefox_cookies(self, mock_bc):
        """从Firefox读取Cookie"""
        mock_cookie = MagicMock()
        mock_cookie.name = "uid"
        mock_cookie.value = "456"
        mock_bc.firefox.return_value = [mock_cookie]

        result = get_cookies_from_browser("firefox")
        assert result == {"uid": "456"}


class TestGetCookies:
    """get_cookies 测试"""

    def test_returns_cached_cookie(self, tmp_path, sample_config):
        """配置文件中有Cookie时直接返回"""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(sample_config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None):
            result = get_cookies()
            assert result == {"sessionid": "test123"}

    def test_reads_from_browser_when_no_cookie(self, tmp_path):
        """配置无Cookie时从浏览器读取"""
        config = {"browser": "chrome", "cookie": {}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None), \
             patch("src.config.get_cookies_from_browser", return_value={"sid": "val"}):
            result = get_cookies()
            assert result == {"sid": "val"}


class TestReloadConfig:
    """reload_config 测试"""

    def test_clears_cache_and_reloads(self, tmp_path, sample_config):
        """清除缓存并重新加载"""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(sample_config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", {"old": "cache"}):
            config = reload_config()
            assert config["browser"] == "chrome"


class TestInitDataDirs:
    """init_data_dirs 测试"""

    def test_creates_data_directories(self, tmp_path, sample_config):
        """创建数据目录"""
        data_dir = tmp_path / "my_data"
        sample_config["data_dir"] = str(data_dir)
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(sample_config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None):
            dirs = init_data_dirs()
            assert dirs["videos"].exists()
            assert dirs["audio"].exists()
            assert dirs["transcripts"].exists()
            assert dirs["analysis"].exists()

    def test_existing_directories_no_error(self, tmp_path, sample_config):
        """目录已存在时不报错"""
        data_dir = tmp_path / "existing"
        for sub in ["videos", "audio", "transcripts", "analysis"]:
            (data_dir / sub).mkdir(parents=True)
        sample_config["data_dir"] = str(data_dir)
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(sample_config), encoding="utf-8")

        with patch("src.config.CONFIG_FILE", config_file), \
             patch("src.config._config_cache", None):
            dirs = init_data_dirs()
            assert all(d.exists() for d in dirs.values())
