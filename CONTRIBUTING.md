# Contributing Guide

感谢你的贡献！请阅读以下指南。

## 开发环境

```bash
git clone https://github.com/mengyuchun/-Douyin_video_analysis_tool.git
cd Douyin_video_analysis_tool
conda create -n data_env python=3.10 -y
conda activate data_env
pip install -r requirements.txt
```

## 提交规范

使用 Conventional Commits：

```
feat: 新功能
fix: 修复 Bug
docs: 文档更新
refactor: 重构
test: 测试
chore: 构建/工具
```

## Pull Request 流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/your-feature`
3. 提交更改：`git commit -m "feat: add xxx"`
4. 推送分支：`git push origin feat/your-feature`
5. 创建 Pull Request

## 代码规范

- Python 3.10+，使用 type hints
- 异步 IO 用 `asyncio`，CPU 密集用 `run_in_executor`
- 新功能需附带测试
- 运行测试：`python -m pytest tests/`

## 报告问题

使用 [Issue 模板](https://github.com/mengyuchun/-Douyin_video_analysis_tool/issues/new/choose) 提交 Bug 或功能建议。
