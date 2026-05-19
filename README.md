# 🎬 Douyin Video Analysis Tool

<p align="center">
  <strong>批量下载抖音视频 → 转音频 → 语音转文本 → 大模型结构化分析</strong>
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

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🎥 **批量下载** | 自动解析分享口令/短链接/标准链接，批量下载无水印视频 |
| 🔊 **视频转音频** | 自动提取音频轨道（mp3/wav/aac） |
| 📝 **语音转文本** | 3 种方案：FunASR 本地离线 / 阿里云 DashScope / Whisper |
| 🤖 **大模型分析** | 3 种方案：DashScope / Ollama 本地 / OpenAI 兼容接口 |
| 🚀 **一键全流程** | 下载 → 转音频 → 转文本 → 分析，全自动 |
| 🧪 **134 个测试** | 88% 覆盖率，稳定可靠 |

## 📦 Quick Start

```bash
# 1. 克隆仓库
git clone https://github.com/mengyuchun/-Douyin_video_analysis_tool.git
cd Douyin_video_analysis_tool

# 2. 创建环境
conda create -n data_env python=3.10 -y
conda activate data_env

# 3. 安装依赖
pip install -r requirements.txt

# 4. 下载语音识别模型（约 2GB，可选）
python download_models.py

# 5. 配置
cp config.example.json config.json
# 编辑 config.json，填写 API Key（使用本地模型则无需）

# 6. 运行
python main.py
```

## 🎯 Usage

将抖音链接放入 `links.txt`（每行一个），启动程序选择功能：

```
功能菜单:
  1. 一键全流程 (下载→转音频→转文本→分析)
  2. 仅下载视频
  3. 仅视频转音频
  4. 仅音频转文本
  5. 仅大模型分析
  6. 刷新Cookie
  7. 导入Cookie
  8. 设置并发数
```

<details>
<summary>📄 支持的链接格式</summary>

```
# 分享口令
7.57 03/26 dAT:/ 【@用户】描述 https://v.douyin.com/xxxxx/

# 短链接
https://v.douyin.com/xxxxx/

# 标准链接
https://www.douyin.com/video/7123456789012345678

# 笔记链接
https://www.douyin.com/note/7123456789012345678
```
</details>

<details>
<summary>📊 输出示例（大模型分析结果）</summary>

```json
{
  "Hook_Type": "痛点提问",
  "Hook_Reason": "原句：'你有没有想过为什么...'，通过提问引发共鸣",
  "CTA_Softness": "情绪软植入",
  "Core_Emotion": "制造焦虑",
  "Narrative_Structure": "PAS(痛点-放大-方案)"
}
```
</details>

## ⚙️ Configuration

### 语音识别

| 方案 | 配置 | 需要 Key | 说明 |
|------|------|---------|------|
| FunASR | `stt_provider: "funasr"` | ❌ | **默认**，完全离线，需下载模型 |
| DashScope | `stt_provider: "dashscope"` | ✅ | 阿里云云端识别 |
| Whisper | `stt_provider: "whisper"` | ❌ | 需安装 openai-whisper |

### 大模型

| 方案 | 配置 | 需要 Key | 默认模型 |
|------|------|---------|----------|
| DashScope | `llm_provider: "dashscope"` | ✅ | qwen3.5-flash |
| Ollama | `llm_provider: "ollama"` | ❌ | qwen2.5:7b |
| OpenAI | `llm_provider: "openai"` | ✅ | gpt-3.5-turbo |

## 📁 Project Structure

```
├── main.py                # 入口
├── src/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── parser.py          # 链接解析
│   ├── api.py             # 抖音 API
│   ├── downloader.py      # 视频下载
│   ├── converter.py       # 视频转音频
│   ├── transcriber.py     # 音频转文本
│   └── analyzer.py        # 大模型分析
├── model/                 # 语音模型（需下载）
├── data/                  # 输出目录
│   ├── videos/            # 视频
│   ├── audio/             # 音频
│   ├── transcripts/       # 文本
│   └── analysis/          # 分析结果
└── tests/                 # 134 个测试
```

## 🤝 Contributing

欢迎贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 📄 License

[MIT License](LICENSE)

---

<p align="center">
  ⭐ 如果这个项目对你有帮助，请点个 Star 支持一下！
</p>
