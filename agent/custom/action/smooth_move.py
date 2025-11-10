from .include import *
import random
import time
import math
import pynput.mouse
from pynput.mouse import Button

@AgentServer.custom_action("SmoothMove")
class SmoothMove(CustomAction):
    print(" SmoothMove 自定义动作已加载")

    """
    参数格式:
    {
        "begin": 起始位置
        "end": 结束位置
        "duration": 移动持续时间 (ms)
    }
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        logger.info("SmoothMove 动作开始执行")
        duration = 1000  # 默认持续时间
        begin = [0,0,0,0]   # 随机一点
        end = [0,0,0,0]
        try:
            params = json.loads(argv.custom_action_param)
            duration = params.get("duration", duration)
            begin = params.get("begin", begin)
            end = params.get("end", end)
        except Exception as e:
            logger.warning(f"参数解析失败，使用默认持续时间 {duration} 秒: {e}")
        
        # 测试
        logger.info(f"SmoothMove 参数: begin={begin}, end={end}, duration={duration} ms")
        time.sleep(3)
        human_drag_right(distance=400, duration=0.8)

        return CustomAction.RunResult(success=True)

mouse = pynput.mouse.Controller()
        

        
def bezier_curve(p0, p1, p2, p3, t):
    """三阶贝塞尔曲线"""
    return (1-t)**3 * p0 + 3*(1-t)**2 * t * p1 + 3*(1-t) * t**2 * p2 + t**3 * p3


def human_move(x1, y1, x2, y2, duration=0.3, steps=45):
    """
    更真实的人类鼠标移动模拟（使用 pynput）
    - 使用贝塞尔曲线创建自然路径
    - 非线性速度变化
    - 微小抖动和停顿
    """
    # 生成贝塞尔曲线的控制点,创建更自然的弧线路径
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # 控制点偏移量,距离越远偏移越大
    offset_range = min(distance * 0.3, 100)
    
    # 第一个控制点(靠近起点)
    cp1_x = x1 + (x2 - x1) * 0.3 + random.uniform(-offset_range, offset_range)
    cp1_y = y1 + (y2 - y1) * 0.3 + random.uniform(-offset_range, offset_range)
    
    # 第二个控制点(靠近终点)
    cp2_x = x1 + (x2 - x1) * 0.7 + random.uniform(-offset_range, offset_range)
    cp2_y = y1 + (y2 - y1) * 0.7 + random.uniform(-offset_range, offset_range)
    
    prev_x, prev_y = x1, y1
    
    for i in range(steps + 1):
        t = i / steps
        
        # 使用更复杂的缓动函数,模拟真实的加速和减速
        if t < 0.1:
            # 起始加速
            eased_t = t * 5 * t
        elif t > 0.85:
            # 末尾减速
            eased_t = 1 - (1 - t) ** 2
        else:
            # 中间快速且略有波动
            eased_t = t + random.uniform(-0.02, 0.02)
        
        eased_t = max(0, min(1, eased_t))
        
        # 使用贝塞尔曲线计算位置
        x = bezier_curve(x1, cp1_x, cp2_x, x2, eased_t)
        y = bezier_curve(y1, cp1_y, cp2_y, y2, eased_t)
        
        # 添加微小的随机抖动
        jitter = max(1, distance / 200)
        x += random.uniform(-jitter, jitter)
        y += random.uniform(-jitter, jitter)
        
        print(f"Step {i}/{steps}: Moving to ({x:.2f}, {y:.2f})")
        
        # 使用 pynput 移动鼠标
        mouse.position = (int(x), int(y))
        
        prev_x, prev_y = x, y
        
        # 根据移动距离和阶段动态调整延迟
        if t < 0.1 or t > 0.9:
            delay = (duration / steps) * random.uniform(1.0, 1.3)
        else:
            delay = (duration / steps) * random.uniform(0.6, 0.9)
        
        # 偶尔添加微小停顿
        if random.random() < 0.05:
            delay += random.uniform(0.001, 0.01)
        
        time.sleep(delay)


def human_drag(x1, y1, x2, y2, duration=0.6, steps=50, button='left'):
    """
    模拟人类拖动鼠标操作（使用 pynput）
    """
    # 先移动到起点
    print(f"Moving to start position ({x1}, {y1})...")
    mouse.position = (x1, y1)
    time.sleep(random.uniform(0.05, 0.15))
    
    # 按下鼠标按键
    btn = Button.left if button == 'left' else (Button.right if button == 'right' else Button.middle)
    print(f"Pressing {button} button...")
    mouse.press(btn)
    time.sleep(random.uniform(0.05, 0.1))
    
    # 生成贝塞尔曲线的控制点
    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    offset_range = min(distance * 0.15, 50)
    
    cp1_x = x1 + (x2 - x1) * 0.35 + random.uniform(-offset_range, offset_range)
    cp1_y = y1 + (y2 - y1) * 0.35 + random.uniform(-offset_range, offset_range)
    
    cp2_x = x1 + (x2 - x1) * 0.65 + random.uniform(-offset_range, offset_range)
    cp2_y = y1 + (y2 - y1) * 0.65 + random.uniform(-offset_range, offset_range)
    
    # 开始拖动
    print(f"Dragging from ({x1}, {y1}) to ({x2}, {y2})...")
    for i in range(1, steps + 1):
        t = i / steps
        
        # 拖动时的缓动曲线
        if t < 0.15:
            eased_t = t * 3.5 * t
        elif t > 0.85:
            eased_t = 1 - (1 - t) ** 2.5
        else:
            eased_t = t + random.uniform(-0.015, 0.015)
        
        eased_t = max(0, min(1, eased_t))
        
        # 使用贝塞尔曲线计算位置
        x = bezier_curve(x1, cp1_x, cp2_x, x2, eased_t)
        y = bezier_curve(y1, cp1_y, cp2_y, y2, eased_t)
        
        # 拖动时的抖动更小
        jitter = max(0.5, distance / 300)
        x += random.uniform(-jitter, jitter)
        y += random.uniform(-jitter, jitter)
        
        mouse.position = (int(x), int(y))
        
        # 拖动时的延迟调整
        if t < 0.15 or t > 0.85:
            delay = (duration / steps) * random.uniform(1.1, 1.4)
        else:
            delay = (duration / steps) * random.uniform(0.8, 1.0)
        
        if random.random() < 0.08:
            delay += random.uniform(0.01, 0.03)
        
        time.sleep(delay)
    
    # 到达目标后短暂停顿再释放
    time.sleep(random.uniform(0.05, 0.12))
    
    # 释放鼠标按键
    print(f"Releasing {button} button...")
    mouse.release(btn)
    print("Drag completed!")


def human_drag_right(distance=300, duration=0.6):
    """向右拖动鼠标的便捷函数"""
    start_x, start_y = mouse.position
    end_x = start_x + distance
    end_y = start_y + random.randint(-2, 2)
    
    human_drag(start_x, start_y, end_x, end_y, duration=duration)






