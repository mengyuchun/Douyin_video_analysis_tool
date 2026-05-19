"""src.parser.py 测试"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.parser import (
    extract_urls,
    extract_video_id,
    resolve_short_url,
    parse_douyin_link,
    batch_parse_links,
)


class TestExtractUrls:
    """extract_urls 测试"""

    def test_extract_short_link(self):
        """提取 v.douyin.com 短链接"""
        text = "看看这个视频 https://v.douyin.com/abc123/ 很有意思"
        urls = extract_urls(text)
        assert "https://v.douyin.com/abc123/" in urls

    def test_extract_standard_link(self):
        """提取标准视频链接"""
        text = "https://www.douyin.com/video/7123456789"
        urls = extract_urls(text)
        assert "https://www.douyin.com/video/7123456789" in urls

    def test_extract_note_link(self):
        """提取笔记链接"""
        text = "https://www.douyin.com/note/9876543210"
        urls = extract_urls(text)
        assert "https://www.douyin.com/note/9876543210" in urls

    def test_extract_modal_id_link(self):
        """提取带modal_id的链接"""
        text = "https://www.douyin.com/discover?modal_id=111222333"
        urls = extract_urls(text)
        assert "https://www.douyin.com/video/111222333" in urls

    def test_extract_multiple_links(self):
        """提取多个链接"""
        text = """
        https://www.douyin.com/video/111
        https://v.douyin.com/abc/
        https://www.douyin.com/video/222
        """
        urls = extract_urls(text)
        assert len(urls) >= 3

    def test_no_links_returns_empty(self):
        """无链接时返回空列表"""
        text = "这是一段普通文本，没有链接"
        urls = extract_urls(text)
        assert urls == []

    def test_deduplication(self):
        """去重"""
        text = """
        https://www.douyin.com/video/123
        https://www.douyin.com/video/123
        """
        urls = extract_urls(text)
        video_ids = [u.split("/")[-1] for u in urls]
        assert video_ids.count("123") == 1

    def test_modal_id_not_duplicated_with_standard(self):
        """modal_id与标准链接不重复"""
        text = """
        https://www.douyin.com/video/123
        modal_id=123
        """
        urls = extract_urls(text)
        video_ids = [u.split("/")[-1] for u in urls]
        assert video_ids.count("123") == 1


class TestExtractVideoId:
    """extract_video_id 测试"""

    def test_standard_url(self):
        """标准链接提取ID"""
        url = "https://www.douyin.com/video/7123456789"
        assert extract_video_id(url) == "7123456789"

    def test_note_url(self):
        """笔记链接提取ID"""
        url = "https://www.douyin.com/note/9876543210"
        assert extract_video_id(url) == "9876543210"

    def test_modal_id_url(self):
        """modal_id提取ID"""
        url = "https://www.douyin.com/discover?modal_id=111222333"
        assert extract_video_id(url) == "111222333"

    def test_invalid_url_returns_none(self):
        """无效链接返回None"""
        url = "https://www.douyin.com/user/123"
        assert extract_video_id(url) is None

    def test_empty_url_returns_none(self):
        """空链接返回None"""
        assert extract_video_id("") is None

    def test_url_with_extra_params(self):
        """带额外参数的链接"""
        url = "https://www.douyin.com/video/123?previous_page=homepage"
        assert extract_video_id(url) == "123"


class TestResolveShortUrl:
    """resolve_short_url 测试"""

    @pytest.mark.asyncio
    async def test_redirect_302(self):
        """302重定向提取Location"""
        mock_resp = MagicMock()
        mock_resp.status_code = 302
        mock_resp.headers = {"location": "https://www.douyin.com/video/123"}

        with patch("src.parser.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await resolve_short_url("https://v.douyin.com/abc/")
            assert result == "https://www.douyin.com/video/123"

    @pytest.mark.asyncio
    async def test_redirect_301(self):
        """301重定向"""
        mock_resp = MagicMock()
        mock_resp.status_code = 301
        mock_resp.headers = {"location": "https://www.douyin.com/video/456"}

        with patch("src.parser.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await resolve_short_url("https://v.douyin.com/def/")
            assert result == "https://www.douyin.com/video/456"

    @pytest.mark.asyncio
    async def test_200_with_embedded_link(self):
        """200响应中提取链接"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '<html><a href="https://www.douyin.com/video/789">watch</a></html>'

        with patch("src.parser.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await resolve_short_url("https://v.douyin.com/ghi/")
            assert result == "https://www.douyin.com/video/789"

    @pytest.mark.asyncio
    async def test_200_no_link_returns_none(self):
        """200响应但无链接返回None"""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = "<html>no link here</html>"

        with patch("src.parser.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await resolve_short_url("https://v.douyin.com/xyz/")
            assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self):
        """异常返回None"""
        with patch("src.parser.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.get.side_effect = Exception("network error")
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            result = await resolve_short_url("https://v.douyin.com/err/")
            assert result is None


class TestParseDouyinLink:
    """parse_douyin_link 测试"""

    @pytest.mark.asyncio
    async def test_standard_link(self):
        """解析标准链接"""
        text = "https://www.douyin.com/video/123456"
        results = await parse_douyin_link(text)
        assert len(results) == 1
        assert results[0]["video_id"] == "123456"

    @pytest.mark.asyncio
    async def test_note_link(self):
        """解析笔记链接"""
        text = "https://www.douyin.com/note/789012"
        results = await parse_douyin_link(text)
        assert len(results) == 1
        assert results[0]["video_id"] == "789012"

    @pytest.mark.asyncio
    async def test_no_links(self):
        """无链接返回空"""
        text = "普通文本"
        results = await parse_douyin_link(text)
        assert results == []

    @pytest.mark.asyncio
    async def test_short_link_resolved(self):
        """短链接解析"""
        with patch("src.parser.resolve_short_url", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = "https://www.douyin.com/video/999"
            text = "https://v.douyin.com/short/"
            results = await parse_douyin_link(text)
            assert len(results) == 1
            assert results[0]["video_id"] == "999"

    @pytest.mark.asyncio
    async def test_short_link_resolve_fails(self):
        """短链接解析失败"""
        with patch("src.parser.resolve_short_url", new_callable=AsyncMock) as mock_resolve:
            mock_resolve.return_value = None
            text = "https://v.douyin.com/bad/"
            results = await parse_douyin_link(text)
            assert results == []


class TestBatchParseLinks:
    """batch_parse_links 测试"""

    @pytest.mark.asyncio
    async def test_multiple_inputs(self):
        """批量解析多条输入"""
        inputs = [
            "https://www.douyin.com/video/111",
            "https://www.douyin.com/video/222",
        ]
        results = await batch_parse_links(inputs)
        ids = [r["video_id"] for r in results]
        assert "111" in ids
        assert "222" in ids

    @pytest.mark.asyncio
    async def test_deduplication(self):
        """批量解析去重"""
        inputs = [
            "https://www.douyin.com/video/111",
            "https://www.douyin.com/video/111",
        ]
        results = await batch_parse_links(inputs)
        ids = [r["video_id"] for r in results]
        assert ids.count("111") == 1

    @pytest.mark.asyncio
    async def test_empty_input(self):
        """空输入返回空"""
        results = await batch_parse_links([])
        assert results == []
