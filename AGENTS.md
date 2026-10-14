# AGENTS.md - Agent 协作须知

## 关键背景：本项目文件被透明加密

本机装有公司透明加密软件（文件头特征 `%TSD-Header-###%`，天锐绿盾类 DLP）。
磁盘上的 `.py` 等文件是密文，只有**授权进程**读文件时驱动才解密：

| 进程 | 读到的内容 |
|---|---|
| PyCharm（用户编辑器） | 明文 |
| `venv\Scripts\python.exe` | **明文** |
| PowerShell（Get-Content 等） | 密文 |
| JetBrains MCP 插件后端（ide_read_file / ide_search_text） | 密文 |

## 读取项目源码的正确方式

**用 venv 的 python.exe 读**（已验证可行）：

```powershell
@'
from pathlib import Path
print(Path(r"com/hym/client/AgentClient.py").read_text(encoding="utf-8", errors="replace"))
'@ | Set-Content -Encoding UTF8 read_tmp.py
& venv\Scripts\python.exe read_tmp.py
```

注意：
- 临时脚本本身会被加密系统锁定（读可以、删除报"拒绝访问"），
  尽量复用同一个临时文件名，最后请用户在 PyCharm 里手动删除
- MCP 工具（ide_diagnostics 等）可用于诊断，但读文件内容无效
- `git show` 只对已提交进 .git 的对象可读（git 对象库未加密）

## 不要浪费时间尝试的方式

- `Get-Content` / `type` / 直接 cat → 密文
- `mcp__jetbrains_index.ide_read_file` → 密文（后端进程未授权）
- 强行删除被锁文件（PowerShell/python 都会 WinError 5）→ 请用户手动删
- 任何进程写入的新文件都会被加密系统接管（python 写入明文，落盘即加密，授权进程仍可读回明文）

## 项目环境速览

- Python 3.13（venv），包：langchain 1.4.4 / langgraph 1.2.14 /
  langchain-openai 1.7.0 / python-dotenv
- 模型：智谱 glm-4-flash（OpenAI 兼容端点），配置在 `env/.env`
  （API_KEY / BASE_URL / MODEL_NAME；已加入 .gitignore，勿入 git）
- 学习路线：工具调用 Agent（已完成）→ 多工具编排 + 多轮对话（进行中，
  PlanTrip.py）→ RAG（暂不需要向量库）
