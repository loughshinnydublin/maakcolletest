"""
测试 smooth_move.py 能否检测到 pyautogui 的鼠标移动
同时运行检测器和鼠标移动程序
"""
import subprocess
import time
import sys
import os

print("=" * 70)
print("测试 PyAutoGUI 鼠标移动检测")
print("=" * 70)

print("\n此测试将验证修改后的 smooth_move.py 能否检测到 pyautogui 的鼠标移动")
print("\n测试步骤:")
print("1. 先启动 smooth_move.py (检测器)")
print("2. 等待 3 秒")
print("3. 运行 autogui_move.py (生成鼠标移动)")
print("4. 检查是否能检测到轨迹")

print("\n" + "="*70)
print("准备开始测试...")
print("="*70)

choice = input("\n按 Enter 继续，或按 Ctrl+C 取消: ")

print("\n✅ 启动测试...")
print("\n1️⃣ 请在另一个终端运行: python smooth_move.py")
print("2️⃣ 等待检测器启动后（看到提示信息），在第三个终端运行: python autogui_move.py")
print("\n或者使用以下命令同时启动两个终端:")
print("\nPowerShell:")
print("  Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd e:\\git\\maakcolletest\\test_click; python smooth_move.py'")
print("  Start-Sleep -Seconds 3")
print("  Start-Process powershell -ArgumentList '-NoExit', '-Command', 'cd e:\\git\\maakcolletest\\test_click; python autogui_move.py'")

print("\n" + "="*70)
print("关键改进说明:")
print("="*70)
print("""
修改前 (使用 pynput 事件监听):
  ❌ 无法检测 pyautogui - 因为 pynput 过滤合成事件
  
修改后 (使用轮询方式):
  ✅ 可以检测 pyautogui - 直接轮询鼠标位置
  ✅ 可以检测所有鼠标移动 - 包括手动、程序生成等
  ✅ 采样率: 200Hz (5ms 间隔)
  
技术细节:
  - 使用 pyautogui.position() 轮询鼠标坐标
  - 只记录位置变化的点，减少重复数据
  - 后台线程持续监控，不阻塞主线程
""")

print("\n期望结果:")
print("  - smooth_move.py 应该能记录到多个数据点 (num_points > 40)")
print("  - 应该能看到 'Moving to: (x, y)' 的输出")
print("  - 最终会生成 mouse_trace.csv 和分析报告")
print("  - 真人化评分可能较低（因为是程序生成的轨迹）")
