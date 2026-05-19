"""src.analyzer.py 测试"""
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.analyzer import (
    DashScopeProvider,
    OllamaProvider,
    OpenAIProvider,
    get_llm_provider,
    parse_llm_output,
    save_json,
    save_markdown,
    analyze_single,
    batch_analyze,
)


class TestParseLlmOutput:
    """parse_llm_output 测试"""

    def test_valid_json(self):
        """直接JSON"""
        text = '{"key": "value", "num": 42}'
        result = parse_llm_output(text)
        assert result == {"key": "value", "num": 42}

    def test_json_in_code_block(self):
        """代码块中的JSON"""
        text = '```json\n{"key": "value"}\n```'
        result = parse_llm_output(text)
        assert result == {"key": "value"}

    def test_json_with_surrounding_text(self):
        """前后有文字的JSON"""
        text = '这是分析结果：\n{"key": "value"}\n以上是结果。'
        result = parse_llm_output(text)
        assert result == {"key": "value"}

    def test_invalid_json_returns_raw(self):
        """无效JSON返回原始文本"""
        text = "这不是JSON格式的输出"
        result = parse_llm_output(text)
        assert result == {"raw_output": text}

    def test_empty_string(self):
        """空字符串"""
        result = parse_llm_output("")
        assert result == {"raw_output": ""}

    def test_nested_json(self):
        """嵌套JSON"""
        text = '{"data": {"nested": true}, "list": [1, 2, 3]}'
        result = parse_llm_output(text)
        assert result["data"]["nested"] is True
        assert result["list"] == [1, 2, 3]

    def test_json_with_extra_spaces_in_code_block(self):
        """代码块中有额外空格"""
        text = '```json  \n  {"key": "value"}  \n  ```'
        result = parse_llm_output(text)
        assert result == {"key": "value"}


class TestSaveJson:
    """save_json 测试"""

    def test_save_json_file(self, tmp_path):
        """保存JSON文件"""
        text_file = tmp_path / "test.txt"
        text_file.write_text("内容", encoding="utf-8")

        result_data = {"title": "测试", "summary": "摘要"}
        result = save_json(result_data, str(text_file))

        assert result.endswith("_分析结果.json")
        saved = json.loads(Path(result).read_text(encoding="utf-8"))
        assert saved["title"] == "测试"


class TestSaveMarkdown:
    """save_markdown 测试"""

    def test_save_markdown_file(self, tmp_path):
        """保存Markdown文件"""
        text_file = tmp_path / "test.txt"
        text_file.write_text("内容", encoding="utf-8")

        result_data = {
            "title": "测试标题",
            "keywords": ["关键词1", "关键词2"],
            "details": {"key": "value"},
        }
        result = save_markdown(result_data, str(text_file), "内容摘要")

        assert result.endswith("_分析报告.md")
        content = Path(result).read_text(encoding="utf-8")
        assert "测试标题" in content
        assert "关键词1" in content
        assert "内容摘要" in content

    def test_markdown_format(self, tmp_path):
        """Markdown格式正确"""
        text_file = tmp_path / "test.txt"
        text_file.write_text("内容", encoding="utf-8")

        result_data = {"section": ["item1", "item2"]}
        result_path = save_markdown(result_data, str(text_file), "模板")
        content = Path(result_path).read_text(encoding="utf-8")

        assert "# 分析报告" in content
        assert "- item1" in content
        assert "- item2" in content
        assert "---" in content


class TestGetLlmProvider:
    """get_llm_provider 测试"""

    def test_dashscope_provider(self):
        """阿里云百炼 DashScope"""
        with patch("src.analyzer.load_config", return_value={
            "llm_provider": "dashscope",
            "llm_api_key": "test_key",
            "llm_model": "qwen3.5-flash",
        }):
            provider = get_llm_provider()
            assert isinstance(provider, DashScopeProvider)

    def test_openai_provider(self):
        """OpenAI"""
        with patch("src.analyzer.load_config", return_value={
            "llm_provider": "openai",
            "llm_api_key": "test_key",
            "llm_model": "gpt-3.5-turbo",
            "llm_base_url": "https://api.openai.com/v1",
        }):
            provider = get_llm_provider()
            assert isinstance(provider, OpenAIProvider)

    def test_ollama_provider(self):
        """本地 Ollama"""
        with patch("src.analyzer.load_config", return_value={
            "llm_provider": "ollama",
            "ollama_base_url": "http://localhost:11434/v1",
            "ollama_model": "qwen2.5:7b",
        }):
            provider = get_llm_provider()
            assert isinstance(provider, OllamaProvider)

    def test_no_api_key_raises(self):
        """无API Key抛异常"""
        with patch("src.analyzer.load_config", return_value={
            "llm_provider": "dashscope",
            "llm_api_key": "",
        }):
            with pytest.raises(Exception, match="llm_api_key"):
                get_llm_provider()

    def test_unknown_provider_raises(self):
        """未知提供商抛异常"""
        with patch("src.analyzer.load_config", return_value={
            "llm_provider": "unknown",
            "llm_api_key": "test_key",
        }):
            with pytest.raises(Exception, match="不支持"):
                get_llm_provider()


class TestDashScopeProvider:
    """DashScopeProvider 测试"""

    @pytest.mark.asyncio
    async def test_success(self):
        """成功调用"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": '{"result": "ok"}'}}]
        }

        with patch("src.analyzer.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = DashScopeProvider("test_key")
            result = await provider.chat("prompt", "content")
            assert result == '{"result": "ok"}'

    @pytest.mark.asyncio
    async def test_failure(self):
        """调用失败"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": {"message": "rate limit"}}

        with patch("src.analyzer.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = DashScopeProvider("test_key")
            with pytest.raises(Exception, match="DashScope调用失败"):
                await provider.chat("prompt", "content")


class TestOpenAIProvider:
    """OpenAIProvider 测试"""

    @pytest.mark.asyncio
    async def test_success(self):
        """成功调用"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }

        with patch("src.analyzer.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = OpenAIProvider("test_key")
            result = await provider.chat("prompt", "content")
            assert result == "response"

    @pytest.mark.asyncio
    async def test_failure(self):
        """调用失败"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": {"message": "invalid key"}}

        with patch("src.analyzer.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = OpenAIProvider("test_key")
            with pytest.raises(Exception, match="OpenAI调用失败"):
                await provider.chat("prompt", "content")


class TestOllamaProvider:
    """OllamaProvider 测试"""

    @pytest.mark.asyncio
    async def test_success(self):
        """成功调用"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "response"}}]
        }

        with patch("src.analyzer.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = OllamaProvider()
            result = await provider.chat("prompt", "content")
            assert result == "response"

    @pytest.mark.asyncio
    async def test_failure(self):
        """调用失败"""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"error": "model not found"}

        with patch("src.analyzer.httpx.AsyncClient") as MockClient:
            instance = AsyncMock()
            instance.post.return_value = mock_resp
            instance.__aenter__ = AsyncMock(return_value=instance)
            instance.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = instance

            provider = OllamaProvider()
            with pytest.raises(Exception, match="Ollama调用失败"):
                await provider.chat("prompt", "content")


class TestAnalyzeSingle:
    """analyze_single 测试"""

    @pytest.mark.asyncio
    async def test_success(self, tmp_path):
        """成功分析"""
        text_file = tmp_path / "test.txt"
        text_file.write_text("视频文案内容", encoding="utf-8")
        analysis_dir = tmp_path / "analysis"
        analysis_dir.mkdir()
        dirs = {"videos": tmp_path, "audio": tmp_path, "transcripts": tmp_path, "analysis": analysis_dir}

        mock_llm = AsyncMock()
        mock_llm.chat.return_value = '{"title": "测试", "summary": "摘要"}'

        with patch("src.analyzer.load_config", return_value={
            "output_json": True,
            "output_markdown": True,
        }), patch("src.analyzer.init_data_dirs", return_value=dirs):
            result = await analyze_single(mock_llm, str(text_file), "prompt", "模板")
            assert result is True
            assert (analysis_dir / "test_分析结果.json").exists()
            assert (analysis_dir / "test_分析报告.md").exists()

    @pytest.mark.asyncio
    async def test_empty_text(self, tmp_path):
        """空文本跳过"""
        text_file = tmp_path / "empty.txt"
        text_file.write_text("", encoding="utf-8")

        mock_llm = AsyncMock()
        result = await analyze_single(mock_llm, str(text_file), "prompt", "模板")
        assert result is False

    @pytest.mark.asyncio
    async def test_llm_exception(self, tmp_path):
        """LLM调用异常"""
        text_file = tmp_path / "test.txt"
        text_file.write_text("内容", encoding="utf-8")

        mock_llm = AsyncMock()
        mock_llm.chat.side_effect = Exception("API error")

        result = await analyze_single(mock_llm, str(text_file), "prompt", "模板")
        assert result is False


class TestBatchAnalyze:
    """batch_analyze 测试"""

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """空列表返回空"""
        result = await batch_analyze([])
        assert result == []

    @pytest.mark.asyncio
    async def test_batch_success(self, tmp_path):
        """批量分析成功"""
        text_files = []
        for i in range(2):
            f = tmp_path / f"test{i}.txt"
            f.write_text(f"内容{i}", encoding="utf-8")
            text_files.append(str(f))

        mock_llm = AsyncMock()
        mock_llm.chat.return_value = '{"title": "测试"}'

        with patch("src.analyzer.get_llm_provider", return_value=mock_llm), \
             patch("src.analyzer.load_config", return_value={
                 "output_json": True,
                 "output_markdown": True,
             }), \
             patch("builtins.input", return_value="1"):
            result = await batch_analyze(text_files)
            # 每个文件生成json和md两个文件
            assert len(result) == 4
