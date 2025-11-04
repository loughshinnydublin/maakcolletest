import pyautogui, random, time, math

pyautogui.FAILSAFE = False
print(pyautogui.size())


def human_move(x1, y1, x2, y2, duration=1.5, steps=120):
    for i in range(steps):
        t = i / steps
        # ease in-out
        t = -0.5 * (math.cos(math.pi * t) - 1)
        # 随机偏移与速度
        x = x1 + (x2 - x1) * t + random.uniform(-1, 1)
        y = y1 + (y2 - y1) * t + random.uniform(-1, 1)
        print(f"Moving to: ({x:.2f}, {y:.2f})")
        pyautogui.moveTo(x, y)

        time.sleep((duration / steps) * random.uniform(0.8, 1.2))


if __name__ == "__main__":
    start_x, start_y = pyautogui.position()
    end_x = start_x + random.randint(-300, 300)
    end_y = start_y + random.randint(-300, 300)
    human_move(start_x, start_y, end_x, end_y)