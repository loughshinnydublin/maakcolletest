# 鼠标移动检测问题说明

## 问题原因

`smooth_move.py` 无法检测到 `autogui_move.py` 移动鼠标的轨迹，原因如下：

### 1. 技术层面

**PyAutoGUI (autogui_move.py)**

- 使用 Win32 API 的 `SendInput()` 函数直接向系统发送输入事件
- 生成的是"合成事件"或"模拟事件"
- 绕过了正常的硬件输入队列

**Pynput (smooth_move.py)**

- 使用 Windows 底层钩子 (Low-level Mouse Hook) 监听鼠标事件
- 主要捕获来自物理硬件的输入事件
- 可能会过滤掉标记为 `LLMHF_INJECTED` 的合成事件

### 2. Windows 事件标记

Windows 会为通过 API 注入的鼠标事件添加 `LLMHF_INJECTED` 标记：

```c
// Windows 钩子回调中可以检测到
if (pMouseStruct->flags & LLMHF_INJECTED) {
    // 这是程序生成的事件，不是真实硬件输入
}
```

`pynput` 的底层实现可能会过滤这些事件，导致无法捕获。

## 解决方案

### 方案 1: 使用 pynput 移动鼠标（推荐）✅

使用 `pynput.mouse.Controller` 来移动鼠标，这样 `pynput.mouse.Listener` 就能检测到：

```python
from pynput.mouse import Controller

mouse = Controller()
mouse.position = (100, 100)  # 可被 pynput.Listener 检测
```

**文件**: `pynput_move.py` (已创建)

### 方案 2: 使用 Win32 API 钩子

直接使用 Windows API 创建全局钩子，不过滤任何事件：

```python
import win32api
import win32con

def mouse_callback(nCode, wParam, lParam):
    # 处理所有鼠标事件，包括合成事件
    return win32api.CallNextHookEx(None, nCode, wParam, lParam)

hook = win32api.SetWindowsHookEx(
    win32con.WH_MOUSE_LL,
    mouse_callback,
    None, 0
)
```

### 方案 3: 使用截图对比法

定期截图并比较鼠标位置变化（性能较低）：

```python
import pyautogui
import time

prev_pos = pyautogui.position()
while True:
    time.sleep(0.01)
    curr_pos = pyautogui.position()
    if curr_pos != prev_pos:
        print(f"鼠标移动: {prev_pos} -> {curr_pos}")
        prev_pos = curr_pos
```

### 方案 4: 修改 pynput 源码

修改 `pynput` 的底层代码，移除对 `LLMHF_INJECTED` 标记的过滤。

## 测试验证

### 测试 1: PyAutoGUI (预期失败)

```bash
# 终端 1
python smooth_move.py

# 终端 2  
python autogui_move.py
```

**结果**: ❌ 无法检测到移动

### 测试 2: Pynput (预期成功)

```bash
# 终端 1
python smooth_move.py

# 终端 2
python pynput_move.py
```

**结果**: ✅ 可以检测到移动

### 测试 3: 手动移动 (预期成功)

```bash
python smooth_move.py
# 然后手动移动鼠标
```

**结果**: ✅ 可以检测到移动

## 对比表

| 方式 | 移动方法 | 能被 pynput 检测 | 速度 | 真实度 |
|------|---------|----------------|------|--------|
| PyAutoGUI | SendInput API | ❌ | 快 | 低 |
| Pynput | 同库移动 | ✅ | 中 | 中 |
| 真实硬件 | 物理鼠标 | ✅ | - | 高 |
| Win32 Hook | 底层钩子 | ✅ | 快 | 低 |

## 推荐使用

**如果需要被检测到**: 使用 `pynput_move.py`

**如果需要高性能自动化**: 使用 `autogui_move.py`（但无法被 pynput 监听）

**如果需要分析真人操作**: 使用 `smooth_move.py` + 手动操作

## 相关文件

- `autogui_move.py` - 使用 PyAutoGUI 的鼠标移动（无法被检测）
- `pynput_move.py` - 使用 Pynput 的鼠标移动（可以被检测）✅
- `smooth_move.py` - 鼠标轨迹检测和分析工具
- `test_detection.py` - 测试辅助脚本
