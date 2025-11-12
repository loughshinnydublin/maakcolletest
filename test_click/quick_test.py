"""
快速测试：验证 smooth_move.py (轮询版) 能否检测 pyautogui
"""
import time
import threading
import pyautogui
import random
import math

# 模拟简单的鼠标移动
def simple_mouse_move():
    """简单的鼠标移动测试"""
    time.sleep(2)  # 等待检测器启动
    print("\n[测试] 开始移动鼠标...")
    
    start_x, start_y = pyautogui.position()
    end_x = start_x + 200
    end_y = start_y + 100
    
    steps = 30
    for i in range(steps + 1):
        t = i / steps
        x = start_x + (end_x - start_x) * t
        y = start_y + (end_y - start_y) * t
        pyautogui.moveTo(int(x), int(y))
        time.sleep(0.02)
    
    print("[测试] 鼠标移动完成！")
    print("[测试] 等待 2 秒后自动停止...")
    time.sleep(2)

# 启动测试
if __name__ == "__main__":
    print("="*60)
    print("PyAutoGUI 检测能力测试")
    print("="*60)
    print("\n这个脚本会:")
    print("1. 模拟一个简单的鼠标移动")
    print("2. 如果 smooth_move.py 在运行，应该能检测到")
    print("\n请确保已经启动了 smooth_move.py (在另一个终端)")
    print("\n将在 3 秒后开始移动鼠标...")
    
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    simple_mouse_move()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print("\n请查看 smooth_move.py 的输出:")
    print("  - 应该能看到记录的数据点 (num_points 应该 > 0)")
    print("  - 应该有 mouse_trace.csv 文件生成")
    print("\n如果检测到数据点，说明修改成功！✅")
    print("如果没有检测到数据点，说明还有问题 ❌")
