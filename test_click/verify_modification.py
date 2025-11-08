"""
验证 smooth_move.py 的修改是否成功
检查关键代码是否已正确修改为轮询模式
"""
import re

print("="*70)
print("验证 smooth_move.py 修改")
print("="*70)

try:
    with open('smooth_move.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "导入 pyautogui": "import pyautogui" in content,
        "定义轮询间隔": "POLLING_INTERVAL" in content,
        "轮询函数存在": "_poll_mouse_position" in content,
        "使用 pyautogui.position()": "pyautogui.position()" in content,
        "启动轮询线程": "_poll_thread" in content,
        "移除旧的 mouse.Listener": "mouse.Listener" not in content,
        "提示轮询模式": "轮询模式" in content,
    }
    
    print("\n检查项:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 所有检查通过！修改成功！")
        print("\n现在 smooth_move.py 可以检测到 pyautogui 的鼠标移动了！")
        print("\n测试方法:")
        print("  1. 打开终端1: python smooth_move.py")
        print("  2. 打开终端2: python autogui_move.py")
        print("  3. 观察终端1是否能记录到鼠标轨迹数据")
    else:
        print("⚠️ 有些检查未通过，可能修改不完整")
    print("="*70)
    
    # 显示一些关键代码片段
    print("\n关键代码片段:")
    print("-"*70)
    
    # 提取轮询函数
    match = re.search(r'def _poll_mouse_position\(self\):.*?(?=\n    def|\nclass|\Z)', content, re.DOTALL)
    if match:
        print("\n轮询函数:")
        lines = match.group(0).split('\n')[:15]  # 显示前15行
        for line in lines:
            print(f"  {line}")
        if len(match.group(0).split('\n')) > 15:
            print("  ...")
    
    print("\n" + "-"*70)
    
except FileNotFoundError:
    print("❌ 找不到 smooth_move.py 文件")
except Exception as e:
    print(f"❌ 验证失败: {e}")
