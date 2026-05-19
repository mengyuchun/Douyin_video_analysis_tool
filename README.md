# Douyin Video Analysis Tool

<p align="center">
  <strong>Batch download Douyin videos → Extract audio → Speech-to-text → LLM structured analysis</strong>
</p>

<p align="center">
  <a href="https://github.com/mengyuchun/-Douyin_video_analysis_tool/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="Python">
  <a href="https://github.com/mengyuchun/-Douyin_video_analysis_tool/stargazers"><img src="https://img.shields.io/github/stars/mengyuchun/-Douyin_video_analysis_tool?style=social" alt="Stars"></a>
  <a href="https://github.com/mengyuchun/-Douyin_video_analysis_tool/issues"><img src="https://img.shields.io/github/issues/mengyuchun/-Douyin_video_analysis_tool" alt="Issues"></a>
  <img src="https://img.shields.io/badge/tests-134%20passed-brightgreen.svg" alt="Tests">
</p>

<p align="center">
  <a href="README.md">English</a> | <a href="README_cn.md">中文</a>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| **Batch Download** | Auto-parse share links / short URLs / standard URLs, batch download watermark-free videos |
| **Video to Audio** | Extract audio tracks (mp3/wav/aac) |
| **Speech to Text** | 3 options: FunASR offline / Alibaba Cloud DashScope / Whisper |
| **LLM Analysis** | 3 options: DashScope / Ollama local / OpenAI-compatible |
| **One-Click Pipeline** | Download → Audio → Text → Analysis, fully automated |
| **134 Tests** | 88% coverage, stable and reliable |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/mengyuchun/-Douyin_video_analysis_tool.git
cd Douyin_video_analysis_tool

# 2. Create environment
conda create -n data_env python=3.10 -y
conda activate data_env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Download speech model (~2GB, optional)
python download_models.py

# 5. Configure
cp config.example.json config.json
# Edit config.json, fill in API Key (not needed for local models)

# 6. Run
python main.py
```

## Usage

Put Douyin links into `links.txt` (one per line), then start the program:

```
Menu:
  1. Full pipeline (download → audio → text → analysis)
  2. Download video only
  3. Video to audio only
  4. Audio to text only
  5. LLM analysis only
  6. Refresh Cookie
  7. Import Cookie
  8. Set concurrency
```

<details>
<summary>Supported link formats</summary>

```
# Share command (copied from Douyin app)
7.57 03/26 dAT:/ @user description https://v.douyin.com/xxxxx/

# Short link
https://v.douyin.com/xxxxx/

# Standard link
https://www.douyin.com/video/7123456789012345678

# Note link
https://www.douyin.com/note/7123456789012345678
```

- Lines starting with `#` are comments, blank lines are skipped
- Automatic deduplication
- Auto-extract valid links from share commands
</details>

<details>
<summary>Output example (LLM analysis)</summary>

**Content summary template:**
```json
{
  "title": "Learn Python in 3 minutes",
  "summary": "Video introduces Python basics...",
  "keywords": ["Python", "programming", "tutorial"],
  "category": "Knowledge sharing",
  "sentiment": "Positive"
}
```

**Product analysis template:**
```json
{
  "Hook_Type": "Pain point question",
  "Hook_Reason": "Original: 'Have you ever thought about why...', triggers empathy",
  "CTA_Softness": "Emotional soft placement",
  "Core_Emotion": "Create anxiety",
  "Narrative_Structure": "PAS (Pain-Amplify-Solution)"
}
```
</details>

## Configuration

### Speech Recognition

| Provider | Config Value | API Key Required | Description |
|----------|-------------|------------------|-------------|
| FunASR | `funasr` | No | **Default**, fully offline, requires model download (~2GB) |
| DashScope | `dashscope` | Yes | Alibaba Cloud recognition, requires `stt_api_key` |
| Whisper | `whisper` | No | Requires `openai-whisper` package |

### LLM Provider

| Provider | Config Value | API Key Required | Default Model |
|----------|-------------|------------------|---------------|
| DashScope | `dashscope` | Yes | qwen3.5-flash |
| Ollama | `ollama` | No | qwen2.5:7b |
| OpenAI | `openai` | Yes | gpt-3.5-turbo |

Using Ollama local model:
```bash
# Install Ollama: https://ollama.com
ollama pull qwen2.5:7b
# Edit config.json: "llm_provider": "ollama"
```

### Analysis Templates

| Template | Description |
|----------|-------------|
| Content Summary | Title, summary, keywords, category, sentiment |
| Product Analysis | Product, selling points, promotion method, conversion hooks |
| Sentiment Analysis | Sentiment tendency, tags, intensity |
| Video Product Analysis | Hook type, CTA softness, emotion, narrative structure |
| Custom | User-defined prompt |

## Project Structure

```
├── main.py                # Entry point
├── config.example.json    # Config template
├── download_models.py     # Model download script
├── src/                   # Core modules
│   ├── config.py          # Configuration management
│   ├── parser.py          # Link parsing (share command / short URL / standard)
│   ├── api.py             # Douyin API (A-Bogus signature)
│   ├── downloader.py      # Async video download (concurrency / progress / resume)
│   ├── converter.py       # Video to audio (moviepy)
│   ├── transcriber.py     # Audio to text (FunASR / DashScope / Whisper)
│   └── analyzer.py        # LLM analysis (DashScope / Ollama / OpenAI)
├── model/                 # FunASR speech models (separate download)
├── data/                  # Output directory
│   ├── videos/            # Downloaded videos
│   ├── audio/             # Extracted audio
│   ├── transcripts/       # Transcribed text
│   └── analysis/          # Analysis results (JSON + Markdown)
└── tests/                 # 134 unit tests
```

## Extending

### Adding a new LLM provider

```python
# src/analyzer.py
class NewProvider:
    async def chat(self, prompt: str, content: str) -> str:
        # Call new model API
        ...
```

Add a branch in `get_llm_provider()` and a config entry in `config.json`.

### Adding analysis templates

```python
# src/analyzer.py PROMPT_TEMPLATES
PROMPT_TEMPLATES["new_template"] = {
    "name": "Template Name",
    "prompt": "Your prompt..."
}
```

## Disclaimer and Risk Notice

### Legal Notice

This tool is intended **solely for educational research and internal team use**. Users must bear all legal responsibility for using this tool.

**Strictly prohibited uses:**

- Any commercial use (including but not limited to reselling video content, bulk reposting for profit)
- Infringing others' intellectual property rights (video copyrights belong to authors and platforms)
- Violating applicable laws and regulations
- Bypassing Douyin's technical protection measures (including anti-scraping, DRM, etc.)
- Large-scale, high-frequency scraping that disrupts Douyin's normal operations
- Distributing content obtained through this tool

### Platform Compliance Risks

- Douyin **explicitly prohibits** unauthorized automated data collection
- Using this tool may result in your **Douyin account being banned or restricted**
- Douyin may update anti-scraping strategies at any time, causing this tool to **stop working**
- The A-Bogus signature algorithm used is derived from reverse engineering and may violate platform terms of service

### Data Security

- Credentials like cookies are stored locally in `config.json` — **do not leak them**
- This tool does not upload any user data to third-party servers
- Recommended to run in an isolated environment, avoid using on devices linked to your main account

### AI-Generated Content

- LLM analysis results are for reference only and **do not represent objective facts**
- Do not use AI analysis as the sole basis for decisions
- AI-generated content may contain bias, errors, or hallucinations

### Recommendations

1. Only download and analyze content you have **legal rights to use**
2. Control scraping frequency to avoid burdening the target platform
3. Regularly check and comply with Douyin's latest terms of service
4. Released under [MIT License](LICENSE), **no warranty of any kind**

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT License](LICENSE)

## Acknowledgments

This project was developed with reference to the following open-source projects and technologies:

| Project | Acknowledgment |
|---------|---------------|
| [JoeanAmier/TikTokDownloader](https://github.com/JoeanAmier/TikTokDownloader) | A-Bogus signature algorithm (`abogus.py` ported from `src/encrypt/aBogus.py`) |
| [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) | Douyin Web API interface design reference |
| [modelscope/FunASR](https://github.com/modelscope/FunASR) | Alibaba DAMO Academy FunASR speech recognition model (paraformer-v2), default local offline STT |
| [DashScope](https://dashscope.aliyun.com/) | Alibaba Cloud LLM platform, providing STT and LLM APIs |
| [openai/whisper](https://github.com/openai/whisper) | OpenAI open-source speech recognition model, optional local STT |
| [gmssl-python](https://github.com/emmansun/gmssl) | Chinese national cryptography SM3 library, dependency for A-Bogus signature |

---

<p align="center">
  If this project helps you, please give it a Star!
</p>
