"""src.converter.py 测试"""
import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

import pytest

from src.converter import batch_extract_audio, extract_audio, get_audio_info


class TestExtractAudio:
    """extract_audio 测试"""

    def test_successful_extraction(self, tmp_path):
        """成功提取音频"""
        video_path = tmp_path / "test.mp4"
        video_path.touch()
        output_path = tmp_path / "test.mp3"

        mock_audio = MagicMock()
        mock_audio.write_audiofile = MagicMock()
        mock_audio.close = MagicMock()

        mock_video = MagicMock()
        mock_video.audio = mock_audio
        mock_video.close = MagicMock()

        with patch("src.converter.VideoFileClip", return_value=mock_video):
            result = extract_audio(str(video_path), str(output_path))
            assert result == str(output_path)
            mock_audio.write_audiofile.assert_called_once()

    def test_no_audio_track(self, tmp_path):
        """视频无音频轨返回None"""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        mock_video = MagicMock()
        mock_video.audio = None
        mock_video.close = MagicMock()

        with patch("src.converter.VideoFileClip", return_value=mock_video):
            result = extract_audio(str(video_path))
            assert result is None

    def test_extraction_exception(self, tmp_path):
        """提取异常返回None"""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        with patch("src.converter.VideoFileClip", side_effect=Exception("ffmpeg error")):
            result = extract_audio(str(video_path))
            assert result is None

    def test_default_output_path(self, tmp_path):
        """默认输出路径"""
        video_path = tmp_path / "my_video.mp4"
        video_path.touch()

        mock_audio = MagicMock()
        mock_audio.write_audiofile = MagicMock()
        mock_audio.close = MagicMock()

        mock_video = MagicMock()
        mock_video.audio = mock_audio
        mock_video.close = MagicMock()

        with patch("src.converter.VideoFileClip", return_value=mock_video):
            result = extract_audio(str(video_path))
            assert result is not None
            assert result.endswith(".mp3")

    def test_custom_audio_format(self, tmp_path):
        """自定义音频格式"""
        video_path = tmp_path / "test.mp4"
        video_path.touch()

        mock_audio = MagicMock()
        mock_audio.write_audiofile = MagicMock()
        mock_audio.close = MagicMock()

        mock_video = MagicMock()
        mock_video.audio = mock_audio
        mock_video.close = MagicMock()

        with patch("src.converter.VideoFileClip", return_value=mock_video):
            result = extract_audio(str(video_path), audio_format="wav")
            assert result is not None
            assert result.endswith(".wav")


class TestBatchExtractAudio:
    """batch_extract_audio 测试"""

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """空列表返回空"""
        result = await batch_extract_audio([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_success(self, tmp_path):
        """批量提取成功"""
        video_files = [str(tmp_path / "v1.mp4"), str(tmp_path / "v2.mp4")]
        for f in video_files:
            Path(f).touch()

        with patch("src.converter.extract_audio", return_value="/tmp/test.mp3"):
            result = await batch_extract_audio(video_files)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, tmp_path):
        """批量提取部分失败"""
        video_files = [str(tmp_path / "v1.mp4"), str(tmp_path / "v2.mp4")]
        for f in video_files:
            Path(f).touch()

        with patch("src.converter.extract_audio", side_effect=["/tmp/test.mp3", None]):
            result = await batch_extract_audio(video_files)
            assert len(result) == 1


class TestGetAudioInfo:
    """get_audio_info 测试"""

    def test_success(self, tmp_path):
        """成功获取音频信息"""
        audio_path = tmp_path / "test.mp3"
        audio_path.write_bytes(b"fake audio data" * 100)

        mock_audio = MagicMock()
        mock_audio.duration = 120.5
        mock_audio.close = MagicMock()

        with patch("moviepy.AudioFileClip", return_value=mock_audio):
            result = get_audio_info(str(audio_path))
            assert result is not None
            assert result["duration"] == 120.5
            assert result["format"] == "mp3"
            assert result["filename"] == "test.mp3"

    def test_exception_returns_none(self, tmp_path):
        """异常返回None"""
        audio_path = tmp_path / "bad.mp3"
        audio_path.touch()

        with patch("moviepy.AudioFileClip", side_effect=Exception("codec error")):
            result = get_audio_info(str(audio_path))
            assert result is None
