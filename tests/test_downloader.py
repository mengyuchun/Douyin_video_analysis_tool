"""src.downloader.py 测试"""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.downloader import batch_download_videos, desc_short, download_single_video, generate_filename


class AsyncContextManager:
    """辅助异步上下文管理器"""
    def __init__(self, obj):
        self.obj = obj
    async def __aenter__(self):
        return self.obj
    async def __aexit__(self, *args):
        pass


class TestGenerateFilename:
    """generate_filename 测试"""

    def test_normal_info(self, sample_video_info):
        """正常生成文件名"""
        result = generate_filename(sample_video_info)
        assert "测试作者" in result
        assert "测试视频标题" in result
        assert "1234567890" in result
        assert result.endswith(".mp4")

    def test_missing_fields(self):
        """缺少字段时使用默认值"""
        info = {"video_id": "999"}
        result = generate_filename(info)
        assert "未知作者" in result
        assert "untitled" in result
        assert "999" in result

    def test_empty_info(self):
        """空字典"""
        result = generate_filename({})
        assert "未知作者" in result
        assert "untitled" in result
        assert "unknown" in result

    def test_special_chars_removed(self):
        """特殊字符被移除"""
        info = {
            "video_id": "123",
            "author": "作者/名:称*",
            "desc": '标题?含"有<特殊>字符|',
        }
        result = generate_filename(info)
        for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
            assert char not in result

    def test_long_fields_truncated(self):
        """长字段被截断"""
        info = {
            "video_id": "123",
            "author": "a" * 50,
            "desc": "b" * 100,
        }
        result = generate_filename(info)
        # 作者截断到30字符
        assert "a" * 30 in result
        # 标题截断到50字符
        assert "b" * 50 in result

    def test_whitespace_stripped(self):
        """空白被去除"""
        info = {
            "video_id": "123",
            "author": "  作者  ",
            "desc": "  标题  ",
        }
        result = generate_filename(info)
        assert "作者" in result
        assert "标题" in result


class TestDescShort:
    """desc_short 测试"""

    def test_normal(self):
        """正常截断"""
        info = {"author": "作者名称", "desc": "这是一个视频标题描述"}
        result = desc_short(info)
        assert "作者名称" in result
        assert "_" in result

    def test_empty_fields(self):
        """空字段"""
        result = desc_short({})
        assert result == "_"

    def test_truncation(self):
        """长字段截断"""
        info = {"author": "a" * 20, "desc": "b" * 30}
        result = desc_short(info)
        assert len(result.split("_")[0]) <= 10
        assert len(result.split("_")[1]) <= 15


class TestDownloadSingleVideo:
    """download_single_video 测试"""

    @pytest.mark.asyncio
    async def test_no_download_url(self, tmp_path):
        """无下载地址返回None"""
        info = {"video_id": "123", "download_url": None}
        sem = asyncio.Semaphore(1)
        progress = MagicMock()

        result = await download_single_video(None, info, tmp_path, sem, progress)
        assert result is None

    @pytest.mark.asyncio
    async def test_file_already_exists(self, tmp_path, sample_video_info):
        """文件已存在时跳过"""
        # 创建已存在的文件
        filename = generate_filename(sample_video_info)
        (tmp_path / filename).touch()

        sem = asyncio.Semaphore(1)
        progress = MagicMock()

        result = await download_single_video(None, sample_video_info, tmp_path, sem, progress)
        assert result is not None
        assert str(tmp_path / filename) == result

    @pytest.mark.asyncio
    async def test_successful_download(self, tmp_path, sample_video_info):
        """成功下载"""
        sem = asyncio.Semaphore(1)
        progress = MagicMock()
        progress.add_task.return_value = "task1"

        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "100"}

        async def mock_aiter_bytes(chunk_size=8192):
            yield b"video data"

        mock_resp.aiter_bytes = mock_aiter_bytes
        mock_resp.aclose = AsyncMock()

        mock_client = AsyncMock()
        mock_client.send = AsyncMock(return_value=mock_resp)
        mock_client.build_request = MagicMock(return_value=MagicMock())

        result = await download_single_video(mock_client, sample_video_info, tmp_path, sem, progress)
        assert result is not None
        assert result.endswith(".mp4")

    @pytest.mark.asyncio
    async def test_download_http_error(self, tmp_path, sample_video_info):
        """HTTP错误返回None"""
        sem = asyncio.Semaphore(1)
        progress = MagicMock()
        progress.add_task.return_value = "task1"

        mock_resp = AsyncMock()
        mock_resp.status_code = 403
        mock_resp.aclose = AsyncMock()

        mock_client = AsyncMock()
        mock_client.send = AsyncMock(return_value=mock_resp)
        mock_client.build_request = MagicMock(return_value=MagicMock())

        result = await download_single_video(mock_client, sample_video_info, tmp_path, sem, progress)
        assert result is None

    @pytest.mark.asyncio
    async def test_download_exception(self, tmp_path, sample_video_info):
        """异常返回None"""
        sem = asyncio.Semaphore(1)
        progress = MagicMock()
        progress.add_task.return_value = "task1"

        mock_client = AsyncMock()
        mock_client.stream.side_effect = Exception("network error")

        result = await download_single_video(mock_client, sample_video_info, tmp_path, sem, progress)
        assert result is None


class TestBatchDownloadVideos:
    """batch_download_videos 测试"""

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """空列表返回空"""
        result = await batch_download_videos([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_success(self, tmp_path, sample_video_info):
        """批量下载成功"""
        video_list = [sample_video_info, {**sample_video_info, "video_id": "999"}]
        dirs = {"videos": tmp_path / "videos", "audio": tmp_path / "audio", "transcripts": tmp_path / "transcripts", "analysis": tmp_path / "analysis"}

        with patch("src.downloader.load_config", return_value={"max_concurrent": 2}), \
             patch("src.downloader.init_data_dirs", return_value=dirs), \
             patch("src.downloader.download_single_video", new_callable=AsyncMock) as mock_dl:
            mock_dl.return_value = str(tmp_path / "test.mp4")
            result = await batch_download_videos(video_list)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, tmp_path, sample_video_info):
        """批量下载部分失败"""
        video_list = [sample_video_info, {**sample_video_info, "video_id": "999"}]
        dirs = {"videos": tmp_path / "videos", "audio": tmp_path / "audio", "transcripts": tmp_path / "transcripts", "analysis": tmp_path / "analysis"}

        with patch("src.downloader.load_config", return_value={"max_concurrent": 2}), \
             patch("src.downloader.init_data_dirs", return_value=dirs), \
             patch("src.downloader.download_single_video", new_callable=AsyncMock) as mock_dl:
            mock_dl.side_effect = [str(tmp_path / "test.mp4"), None]
            result = await batch_download_videos(video_list)
            assert len(result) == 1
