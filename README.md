# 抖音短视频批量下载与分析工具

批量下载抖音视频 → 转音频 → 语音转文本 → 大模型结构化分析，全流程自动化。

---

## 目录结构

```
├── main.py                # 主程序入口
├── config.example.json    # 配置模板（复制为 config.json 使用）
├── links.txt              # 链接输入（每行一个抖音链接）
├── download_models.py     # 模型下载脚本
├── requirements.txt       # Python 依赖
├── LICENSE                # MIT 许可证
├── 启动.bat               # Windows 双击启动
├── run.ps1                # PowerShell 启动脚本
├── src/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── parser.py          # 链接解析
│   ├── api.py             # 抖音 API
│   ├── downloader.py      # 视频下载
│   ├── converter.py       # 视频转音频
│   ├── transcriber.py     # 音频转文本
│   ├── analyzer.py        # 大模型分析
│   ├── import_cookie.py   # Cookie 导入工具
│   └── abogus.py          # A-Bogus 签名
├── model/                 # FunASR 本地语音模型（需单独下载，约2GB）
├── data/                  # 数据输出（自动创建）
│   ├── videos/            # 下载的视频
│   ├── audio/             # 提取的音频
│   ├── transcripts/       # 识别的文本
│   └── analysis/          # 分析结果（JSON + Markdown）
└── tests/                 # 测试
```

---

## 环境准备

### 1. 安装 Miniconda

从 https://docs.conda.io/en/latest/miniconda.html 下载安装。

### 2. 创建虚拟环境

```powershell
conda create -n data_env python=3.10 -y
conda activate data_env
```

### 3. 安装依赖

```powershell
cd Douyin_video_analysis_tool
pip install -r requirements.txt
```

### 4. 下载语音识别模型

默认使用本地 FunASR 进行语音识别，需下载模型（约 2GB）：

```powershell
python download_models.py
```

或手动从 ModelScope 下载：
- https://modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
- https://modelscope.cn/models/iic/speech_fsmn_vad_zh-cn-16k-common-pytorch
- https://modelscope.cn/models/iic/punc_ct-transformer_cn-en-common-vocab471067-large

将三个模型文件夹放入项目根目录的 `model/` 文件夹。

如使用云端语音识别（`stt_provider: "dashscope"`），可跳过此步。

### 5. 配置 API Key

编辑 `config.json`，按需填写：

| 用途 | 配置项 | 说明 |
|------|--------|------|
| 云端语音识别 | `stt_api_key` | 阿里云百炼 API Key（使用 `funasr` 本地模式则不需要） |
| 大模型分析 | `llm_api_key` | 阿里云百炼 / OpenAI 的 API Key（使用 `ollama` 本地模式则不需要） |

---

## 快速开始

首次使用：

```powershell
copy config.example.json config.json
```

### 方式一：VS Code 终端（推荐）

```powershell
conda activate data_env
python main.py
```

### 方式二：双击启动

双击 `启动.bat`（首次需先运行 `conda init cmd.exe`）。

### 操作流程

1. 将抖音链接粘贴到 `links.txt`（每行一个，支持分享口令/短链接/标准链接）
2. 启动程序，选择功能编号
3. 等待处理完成，结果保存在 `data/` 目录

---

## 功能菜单

| 编号 | 功能 | 说明 |
|------|------|------|
| 1 | 一键全流程 | 下载 → 转音频 → 转文本 → 大模型分析 |
| 2 | 仅下载视频 | 视频保存到 `data/videos/` |
| 3 | 仅视频转音频 | 音频保存到 `data/audio/` |
| 4 | 仅音频转文本 | 文本保存到 `data/transcripts/` |
| 5 | 仅大模型分析 | 结果保存到 `data/analysis/` |
| 6 | 刷新 Cookie | 清除缓存的 Cookie |
| 7 | 导入 Cookie | 手动粘贴浏览器 Cookie |
| 8 | 设置并发数 | 调整同时下载数量（1-10） |

---

## 配置说明

### config.json 完整配置

```json
{
  "browser": "chrome",
  "data_dir": "data",
  "links_file": "links.txt",
  "max_concurrent": 3,
  "cookie": {},
  "stt_provider": "funasr",
  "stt_api_key": "",
  "whisper_model": "base",
  "funasr_model_dir": "model",
  "llm_provider": "dashscope",
  "llm_api_key": "",
  "llm_model": "qwen3.5-flash",
  "ollama_base_url": "http://localhost:11434/v1",
  "ollama_model": "qwen2.5:7b",
  "output_json": true,
  "output_markdown": true
}
```

### 语音识别（stt_provider）

| 值 | 方案 | 需要 API Key | 说明 |
|----|------|-------------|------|
| `funasr` | 本地 FunASR | 否 | **默认**，使用 `model/` 目录下三个模型，完全离线 |
| `dashscope` | 阿里云云端 | 是 | 需填写 `stt_api_key` |
| `whisper` | 本地 Whisper | 否 | 需安装 `openai-whisper`，模型由 `whisper_model` 控制 |

### 大模型（llm_provider）

| 值 | 方案 | 需要 API Key | 默认模型 |
|----|------|-------------|----------|
| `dashscope` | 阿里云百炼 | 是 | `qwen3.5-flash` |
| `ollama` | 本地 Ollama | 否 | `qwen2.5:7b`（由 `ollama_model` 控制） |
| `openai` | OpenAI 兼容接口 | 是 | `gpt-3.5-turbo` |

使用 Ollama 本地模型：
1. 安装 Ollama：https://ollama.com
2. 拉取模型：`ollama pull qwen2.5:7b`
3. 修改 config.json：`"llm_provider": "ollama"`

### 分析模板

程序内置 5 种分析模板：

| 模板 | 说明 |
|------|------|
| 内容摘要 | 标题、摘要、关键词、类别、情感 |
| 带货分析 | 商品、卖点、推广方式、转化钩子 |
| 情感分析 | 情感倾向、情感标签、强度 |
| 视频带货分析 | Hook类型、CTA软硬度、情绪底色、叙事结构 |
| 自定义 | 用户自行输入提示词 |

---

## 链接格式支持

在 `links.txt` 中每行放一个链接，支持：

```
# 分享口令（从抖音APP复制）
7.57 03/26 dAT:/ 【@用户】描述 https://v.douyin.com/xxxxx/

# 短链接
https://v.douyin.com/xxxxx/

# 标准链接
https://www.douyin.com/video/7123456789012345678

# 笔记链接
https://www.douyin.com/note/7123456789012345678
```

- `#` 开头为注释，空行自动跳过
- 自动去重

---

## Cookie 获取方式

### 方式一：自动读取（默认）

程序尝试从 Chrome 浏览器自动读取 `douyin.com` 的 Cookie。需先在浏览器登录抖音。

### 方式二：手动导入

运行 `python src/import_cookie.py`，按提示粘贴从浏览器复制的 Cookie 字符串。

### 方式三：菜单导入

启动程序后选择功能 7。

---

## 常见问题

**Q: Cookie 读取失败？**
A: 在浏览器登录 douyin.com，或使用功能 7 手动导入 Cookie。

**Q: 语音识别失败？**
A: 默认使用本地 FunASR，无需 API Key。如使用 dashscope，检查 `stt_api_key` 是否正确。

**Q: 大模型分析报错？**
A: 使用 dashscope/openai 需填写 `llm_api_key`；使用 ollama 需先安装并启动 Ollama 服务。

**Q: 下载的视频有水印？**
A: 程序默认获取无水印版本。如有水印可能是 Cookie 过期，刷新 Cookie 后重试。

**Q: 程序中断了怎么办？**
A: 直接重新运行，已下载的文件会自动跳过。

---

## 许可说明

本工具仅供学习和团队内部使用，请遵守抖音平台使用条款和相关法律法规。
