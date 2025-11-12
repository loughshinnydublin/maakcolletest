"""
测试脚本：验证 smooth_move.py 能否检测到不同方式生成的鼠标移动
"""
import subprocess
import time
import sys

print("=" * 60)
print("鼠标移动检测测试")
print("=" * 60)

print("\n选择测试方式:")
print("1. 使用 pyautogui 移动鼠标 (autogui_move.py)")
print("2. 使用 pynput 移动鼠标 (pynput_move.py) - 推荐")
print("3. 手动移动鼠标")

choice = input("\n请选择 (1/2/3): ").strip()

if choice == "1":
    print("\n⚠️ 警告: pyautogui 生成的鼠标移动可能无法被 pynput 检测到!")
    print("这是因为 pyautogui 使用系统级 API，而 pynput 监听硬件事件流。\n")
    time.sleep(2)
    
    print("将启动两个程序:")
    print("1. smooth_move.py (检测器)")
    print("2. autogui_move.py (鼠标移动生成器)")
    print("\n请在 3 秒内切换到终端窗口...")
    time.sleep(3)
    
    print("\n启动检测器 (10秒后自动停止)...")
    print("请在另一个终端运行: python autogui_move.py")
    
elif choice == "2":
    print("\n✅ 使用 pynput 移动鼠标，应该可以被检测到!")
    print("\n将启动两个程序:")
    print("1. smooth_move.py (检测器)")
    print("2. pynput_move.py (鼠标移动生成器)")
    print("\n请同时运行两个脚本:")
    print("  终端1: python smooth_move.py")
    print("  终端2: python pynput_move.py")
    
elif choice == "3":
    print("\n请手动移动鼠标进行测试")
    print("在另一个终端运行: python smooth_move.py")
    
else:
    print("无效选择")
    sys.exit(1)

print("\n" + "=" * 60)
print("测试说明:")
print("=" * 60)
print("""
为什么 pyautogui 无法被 pynput 检测：

1. 事件来源不同：
   - pyautogui: 使用 Win32 API (SendInput) 直接操作鼠标
   - pynput: 监听系统输入事件队列
   
2. 事件过滤：
   - Windows 会标记"合成事件"(LLMHF_INJECTED)
   - pynput 的底层钩子可能过滤掉这些事件
   
3. 解决方案：
   - 使用相同的库: pynput.mouse.Controller 移动 + pynput.mouse.Listener 监听
   - 或使用其他监听方法: win32api 钩子、PIL截图对比等

推荐使用 pynput_move.py 进行测试！
""")
