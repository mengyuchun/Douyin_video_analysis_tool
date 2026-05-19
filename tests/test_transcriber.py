"""src.transcriber.py 测试"""
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.transcriber import (
    LocalWhisper,
    batch_transcribe,
    get_transcriber,
    save_transcript,
    transcribe_single,
)


class TestGetTranscriber:
    """get_transcriber 测试"""

    def test_dashscope_provider(self):
        """DashScope提供商"""
        with patch("src.transcriber.load_config", return_value={
            "stt_provider": "dashscope",
            "stt_api_key": "test_key",
        }):
            transcriber = get_transcriber()
            assert transcriber.__class__.__name__ == "DashScopeSTT"

    def test_dashscope_fallback_key(self):
        """DashScope备用key字段"""
        with patch("src.transcriber.load_config", return_value={
            "stt_provider": "dashscope",
            "dashscope_api_key": "fallback_key",
        }):
            transcriber = get_transcriber()
            assert transcriber.api_key == "fallback_key"

    def test_whisper_provider(self):
        """Whisper提供商"""
        with patch("src.transcriber.load_config", return_value={
            "stt_provider": "whisper",
            "whisper_model": "small",
        }):
            transcriber = get_transcriber()
            assert isinstance(transcriber, LocalWhisper)
            assert transcriber.model_name == "small"

    def test_no_api_key_raises(self):
        """无API Key抛异常"""
        with patch("src.transcriber.load_config", return_value={
            "stt_provider": "dashscope",
            "stt_api_key": "",
        }):
            with pytest.raises(Exception, match="stt_api_key"):
                get_transcriber()

    def test_unknown_provider_raises(self):
        """未知提供商抛异常"""
        with patch("src.transcriber.load_config", return_value={
            "stt_provider": "unknown",
        }):
            with pytest.raises(Exception, match="不支持"):
                get_transcriber()


class TestSaveTranscript:
    """save_transcript 测试"""

    def test_save_txt_file(self, tmp_path):
        """保存文本文件"""
        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        result = save_transcript("识别的文本内容", str(audio_path))
        assert result.endswith(".txt")
        assert Path(result).read_text(encoding="utf-8") == "识别的文本内容"

    def test_output_path_same_stem(self, tmp_path):
        """输出文件名与音频同名"""
        audio_path = tmp_path / "my_audio.wav"
        audio_path.touch()

        result = save_transcript("text", str(audio_path))
        assert Path(result).stem == "my_audio"


class TestLocalWhisper:
    """LocalWhisper 测试"""

    def test_initial_state(self):
        """初始状态"""
        whisper = LocalWhisper("base")
        assert whisper.model_name == "base"
        assert whisper._model is None

    def test_load_model_import_error(self):
        """whisper未安装时抛异常"""
        whisper = LocalWhisper("base")
        with patch.dict("sys.modules", {"whisper": None}):
            with pytest.raises(Exception, match="未安装 whisper"):
                whisper._load_model()

    @pytest.mark.asyncio
    async def test_transcribe_success(self):
        """成功转写"""
        whisper = LocalWhisper("base")
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {"text": "识别结果"}
        whisper._model = mock_model

        result = await whisper.transcribe("/tmp/test.mp3")
        assert result == "识别结果"

    @pytest.mark.asyncio
    async def test_transcribe_empty_result(self):
        """转写结果为空"""
        whisper = LocalWhisper("base")
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {}
        whisper._model = mock_model

        result = await whisper.transcribe("/tmp/test.mp3")
        assert result == ""


class TestTranscribeSingle:
    """transcribe_single 测试"""

    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        """成功识别"""
        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        mock_transcriber = AsyncMock()
        mock_transcriber.transcribe.return_value = "识别的文本"

        result = await transcribe_single(mock_transcriber, str(audio_path))
        assert result is not None
        assert result.endswith(".txt")
        assert Path(result).read_text(encoding="utf-8") == "识别的文本"

    @pytest.mark.asyncio
    async def test_empty_result(self, tmp_path):
        """识别结果为空"""
        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        mock_transcriber = AsyncMock()
        mock_transcriber.transcribe.return_value = ""

        result = await transcribe_single(mock_transcriber, str(audio_path))
        assert result is None

    @pytest.mark.asyncio
    async def test_whitespace_only_result(self, tmp_path):
        """识别结果只有空白"""
        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        mock_transcriber = AsyncMock()
        mock_transcriber.transcribe.return_value = "   \n  "

        result = await transcribe_single(mock_transcriber, str(audio_path))
        assert result is None

    @pytest.mark.asyncio
    async def test_exception_returns_none(self, tmp_path):
        """异常返回None"""
        audio_path = tmp_path / "test.mp3"
        audio_path.touch()

        mock_transcriber = AsyncMock()
        mock_transcriber.transcribe.side_effect = Exception("API error")

        result = await transcribe_single(mock_transcriber, str(audio_path))
        assert result is None


class TestBatchTranscribe:
    """batch_transcribe 测试"""

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """空列表返回空"""
        result = await batch_transcribe([])
        assert result == []

    @pytest.mark.asyncio
    async def test_transcriber_init_fails(self):
        """转写器初始化失败"""
        with patch("src.transcriber.get_transcriber", side_effect=Exception("no key")):
            result = await batch_transcribe(["/tmp/test.mp3"])
            assert result == []

    @pytest.mark.asyncio
    async def test_batch_success(self, tmp_path):
        """批量识别成功"""
        audio_files = []
        for i in range(2):
            f = tmp_path / f"audio{i}.mp3"
            f.touch()
            audio_files.append(str(f))

        mock_transcriber = AsyncMock()

        with patch("src.transcriber.get_transcriber", return_value=mock_transcriber), \
             patch("src.transcriber.transcribe_single", new_callable=AsyncMock) as mock_single:
            mock_single.side_effect = [
                str(tmp_path / "audio0.txt"),
                str(tmp_path / "audio1.txt"),
            ]
            result = await batch_transcribe(audio_files)
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_batch_partial_failure(self, tmp_path):
        """批量识别部分失败"""
        audio_files = []
        for i in range(2):
            f = tmp_path / f"audio{i}.mp3"
            f.touch()
            audio_files.append(str(f))

        mock_transcriber = AsyncMock()

        with patch("src.transcriber.get_transcriber", return_value=mock_transcriber), \
             patch("src.transcriber.transcribe_single", new_callable=AsyncMock) as mock_single:
            mock_single.side_effect = [str(tmp_path / "audio0.txt"), None]
            result = await batch_transcribe(audio_files)
            assert len(result) == 1
