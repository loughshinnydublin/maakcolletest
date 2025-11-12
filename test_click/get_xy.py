"""
鼠标点击位置获取工具
使用 pynput 监听鼠标点击，显示点击位置的坐标
适用于 pynput.mouse.click

使用方法:
1. 运行程序: python get_xy.py
2. 在屏幕上点击任意位置
3. 程序会显示点击坐标
4. 按 Esc 键退出

依赖:
pip install pynput
"""

from pynput import mouse, keyboard
import time

class MousePositionCapture:
    def __init__(self):
        self.click_count = 0
        self.running = True
        self.positions = []
        
    def on_click(self, x, y, button, pressed):
        """鼠标点击事件处理"""
        if pressed:  # 只记录按下事件，不记录释放事件
            self.click_count += 1
            button_name = str(button).replace('Button.', '')
            
            print(f"\n[点击 #{self.click_count}]")
            print(f"  坐标: ({x}, {y})")
            print(f"  按键: {button_name}")
            print(f"  时间: {time.strftime('%H:%M:%S')}")
            
            # 保存坐标
            self.positions.append((x, y, button_name))
            
            # 显示适用于 pynput 的代码
            print(f"\n  📝 pynput 代码示例:")
            print(f"     mouse.Controller().position = ({x}, {y})")
            print(f"     mouse.Controller().click(mouse.Button.{button_name}, 1)")
            print(f"  或:")
            print(f"     mouse_controller.position = ({x}, {y})")
            print(f"     mouse_controller.click(mouse.Button.{button_name})")
            print("-" * 60)
    
    def on_press(self, key):
        """键盘按键事件处理"""
        try:
            if key == keyboard.Key.esc:
                print("\n\n检测到 Esc 键，准备退出...")
                self.show_summary()
                self.running = False
                return False  # 停止监听
        except AttributeError:
            pass
    
    def show_summary(self):
        """显示总结"""
        print("\n" + "="*60)
        print("📊 点击记录汇总")
        print("="*60)
        print(f"总点击次数: {self.click_count}")
        
        if self.positions:
            print("\n所有点击位置:")
            for i, (x, y, btn) in enumerate(self.positions, 1):
                print(f"  {i}. ({x:4d}, {y:4d}) - {btn}")
            
            print("\n📋 批量代码示例:")
            print("-"*60)
            print("from pynput.mouse import Controller, Button")
            print("import time")
            print("\nmouse = Controller()")
            print("positions = [")
            for x, y, btn in self.positions:
                print(f"    (({x}, {y}), Button.{btn}),")
            print("]")
            print("\nfor pos, button in positions:")
            print("    mouse.position = pos")
            print("    time.sleep(0.1)")
            print("    mouse.click(button)")
            print("    time.sleep(0.2)")
            print("-"*60)
        
        print("\n程序已退出。")
    
    def start(self):
        """启动监听"""
        print("="*60)
        print("🖱️  鼠标坐标获取工具")
        print("="*60)
        print("\n说明:")
        print("  • 点击屏幕任意位置获取坐标")
        print("  • 支持左键、右键、中键点击")
        print("  • 按 Esc 键退出并显示总结")
        print("  • 坐标可直接用于 pynput.mouse.Controller()")
        print("\n开始监听鼠标点击...")
        print("-"*60)
        
        # 创建监听器
        mouse_listener = mouse.Listener(on_click=self.on_click)
        keyboard_listener = keyboard.Listener(on_press=self.on_press)
        
        # 启动监听
        mouse_listener.start()
        keyboard_listener.start()
        
        # 等待退出
        keyboard_listener.join()
        mouse_listener.stop()


def main():
    """主函数"""
    try:
        capture = MousePositionCapture()
        capture.start()
    except KeyboardInterrupt:
        print("\n\n检测到 Ctrl+C，程序退出。")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        print("请确保已安装 pynput: pip install pynput")


if __name__ == "__main__":
    main()
