from pathlib import Path

p = Path("com/hym/call/MultiCall.py")
t = p.read_text(encoding="utf-8")

# 1. 摘出底部的函数定义块
marker_start = "\n\ndef agent_as_tool"
idx = t.find(marker_start)
assert idx != -1, "未找到函数定义"
func_block = t[idx:].strip()          # 到文件尾
t_without = t[:idx].rstrip() + "\n"   # 剩余部分

# 2. 插入到第一次调用之前
anchor = "weather_expert = agent_as_tool"
pos = t_without.find(anchor)
assert pos != -1, "未找到调用点"
t_new = t_without[:pos] + func_block + "\n\n\n" + t_without[pos:]

p.write_text(t_new, encoding="utf-8")

# 3. 校验：定义行号 < 首次调用行号
lines = t_new.splitlines()
def_line = next(i for i, l in enumerate(lines, 1) if l.startswith("def agent_as_tool"))
call_line = next(i for i, l in enumerate(lines, 1) if "agent_as_tool(" in l and "def " not in l)
print(f"定义在第 {def_line} 行，首次调用在第 {call_line} 行 ->", "顺序正确" if def_line < call_line else "顺序错误!")
