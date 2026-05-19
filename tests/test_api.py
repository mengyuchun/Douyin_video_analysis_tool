"""src.api.py 测试"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.api import batch_get_video_info, clean_title, get_video_info


class TestCleanTitle:
    """clean_title 测试"""

    def test_normal_title(self):
        """正常标题不变"""
        assert clean_title("好看的视频") == "好看的视频"

    def test_remove_special_chars(self):
        """移除非法文件名字符"""
        title = '视频: 标题*含?有<特殊>字符|'
        result = clean_title(title)
        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|', '\n', '\r']:
            assert char not in result

    def test_truncate_long_title(self):
        """长标题截断到80字符"""
        title = "a" * 100
        result = clean_title(title)
        assert len(result) <= 80

    def test_empty_title_returns_untitled(self):
        """空标题返回untitled"""
        assert clean_title("") == "untitled"
        assert clean_title("   ") == "untitled"

    def test_only_special_chars_returns_untitled(self):
        """全特殊字符返回untitled"""
        assert clean_title(":*?<>|") == "untitled"

    def test_newlines_removed(self):
        """换行符被移除"""
        title = "标题\n带换行\r"
        result = clean_title(title)
        assert "\n" not in result
        assert "\r" not in result


class TestGetVideoInfo:
    """get_video_info 测试"""

    @pytest.mark.asyncio
    async def test_success_response(self):
        """成功获取视频信息（iesdouyin API）"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"item_list": [{"desc": "测试视频", "author": {"nickname": "作者A"}, "video": {"play_addr": {"url_list": ["https://example.com/play.mp4"]}, "cover": {"url_list": ["https://example.com/cover.jpg"]}, "duration": 15000}}]}'
        mock_resp.json.return_value = {
            "item_list": [{
                "desc": "测试视频",
                "author": {"nickname": "作者A"},
                "video": {
                    "play_addr": {"url_list": ["https://example.com/play.mp4"]},
                    "cover": {"url_list": ["https://example.com/cover.jpg"]},
                    "duration": 15000,
                },
            }],
        }

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("123", {"sid": "val"})
            assert result is not None
            assert result["video_id"] == "123"
            assert result["author"] == "作者A"
            assert result["duration"] == 15000

    @pytest.mark.asyncio
    async def test_playwm_replaced_with_play(self):
        """playwm替换为play"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status_code": 0,
            "aweme_detail": {
                "desc": "视频",
                "author": {"nickname": "B"},
                "video": {
                    "play_addr": {"url_list": ["https://example.com/playwm/video.mp4"]},
                    "bit_rate": [],
                    "cover": {"url_list": []},
                    "duration": 5000,
                },
            },
        }

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("456", {"sid": "val"})
            assert "playwm" not in result["download_url"]
            assert "play/video.mp4" in result["download_url"]

    @pytest.mark.asyncio
    async def test_http_error_returns_none(self):
        """HTTP错误返回None"""
        mock_resp = MagicMock()
        mock_resp.status_code = 403

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("123", {"sid": "val"})
            assert result is None

    @pytest.mark.asyncio
    async def test_api_error_returns_none(self):
        """API返回错误码"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_code": 2154, "status_msg": "视频不存在"}

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("123", {"sid": "val"})
            assert result is None

    @pytest.mark.asyncio
    async def test_no_aweme_detail_returns_none(self):
        """无aweme_detail返回None"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status_code": 0}

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("123", {"sid": "val"})
            assert result is None

    @pytest.mark.asyncio
    async def test_no_download_url_returns_none(self):
        """无下载地址返回None"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status_code": 0,
            "aweme_detail": {
                "desc": "视频",
                "author": {"nickname": "B"},
                "video": {
                    "play_addr": {"url_list": []},
                    "bit_rate": [],
                    "cover": {"url_list": []},
                    "duration": 5000,
                },
            },
        }

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("123", {"sid": "val"})
            assert result is None

    @pytest.mark.asyncio
    async def test_timeout_returns_none(self):
        """超时返回None"""
        import httpx

        with patch("src.api.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = httpx.TimeoutException("timeout")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await get_video_info("123", {"sid": "val"})
            assert result is None

    @pytest.mark.asyncio
    async def test_uses_provided_client(self):
        """使用传入的client"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "status_code": 0,
            "aweme_detail": {
                "desc": "视频",
                "author": {"nickname": "C"},
                "video": {
                    "play_addr": {"url_list": ["https://example.com/v.mp4"]},
                    "bit_rate": [],
                    "cover": {"url_list": []},
                    "duration": 3000,
                },
            },
        }

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        result = await get_video_info("789", {"sid": "val"}, client=mock_client)
        assert result is not None
        assert result["video_id"] == "789"
        mock_client.get.assert_called_once()


class TestBatchGetVideoInfo:
    """batch_get_video_info 测试"""

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """空列表返回空"""
        result = await batch_get_video_info([], {"sid": "val"})
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_success(self):
        """批量获取成功"""
        video_list = [
            {"video_id": "111"},
            {"video_id": "222"},
        ]

        with patch("src.api.get_video_info", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                {"video_id": "111", "desc": "视频1", "author": "A", "download_url": "url1", "cover_url": None, "duration": 1000},
                {"video_id": "222", "desc": "视频2", "author": "B", "download_url": "url2", "cover_url": None, "duration": 2000},
            ]
            with patch("src.api.load_config", return_value={"max_concurrent": 2}):
                result = await batch_get_video_info(video_list, {"sid": "val"})
                assert len(result) == 2

    @pytest.mark.asyncio
    async def test_partial_failure(self):
        """部分失败"""
        video_list = [
            {"video_id": "111"},
            {"video_id": "222"},
        ]

        with patch("src.api.get_video_info", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                {"video_id": "111", "desc": "视频1", "author": "A", "download_url": "url1", "cover_url": None, "duration": 1000},
                None,
            ]
            with patch("src.api.load_config", return_value={"max_concurrent": 2}):
                result = await batch_get_video_info(video_list, {"sid": "val"})
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_exception_in_batch(self):
        """批量中异常被捕获"""
        video_list = [
            {"video_id": "111"},
            {"video_id": "222"},
        ]

        with patch("src.api.get_video_info", new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [
                Exception("network error"),
                {"video_id": "222", "desc": "视频2", "author": "B", "download_url": "url2", "cover_url": None, "duration": 2000},
            ]
            with patch("src.api.load_config", return_value={"max_concurrent": 2}):
                result = await batch_get_video_info(video_list, {"sid": "val"})
                assert len(result) == 1
