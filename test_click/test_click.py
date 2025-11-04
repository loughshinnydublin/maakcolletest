import time
from pynput import mouse
import pandas as pd
import numpy as np
from threading import Timer

click_data = []
start_time = time.time()
record_duration = 10  # 采集时长（秒）


def on_click(x, y, button, pressed):
    """鼠标点击事件回调"""
    if pressed:
        click_data.append(
            {"timestamp": time.time(), "x": x, "y": y, "button": str(button)}
        )
        print(f"[CLICK] {button} at ({x}, {y})")


def stop_listener(listener):
    """停止监听"""
    listener.stop()
    print("\n采集结束，正在分析...")


def analyze_clicks(data):
    """分析点击数据是否为真人操作"""
    df = pd.DataFrame(data)
    if df.empty:
        print("未检测到点击数据。")
        return


    # 计算时间间隔
    df["dt"] = df["timestamp"].diff()
    intervals = df["dt"].dropna().values

    # 计算统计特征
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    click_rate = len(df) / (df["timestamp"].iloc[-1] - df["timestamp"].iloc[0])

    # 计算点击坐标分布
    x_var = np.var(df["x"])
    y_var = np.var(df["y"])

    print(df)

    print("\n==== 点击数据统计 ====")
    print(f"总点击次数: {len(df)}")
    print(f"平均间隔: {mean_interval:.3f}s")
    print(f"间隔标准差: {std_interval:.3f}s")
    print(f"点击频率: {click_rate:.2f} 次/秒")
    print(f"X方差: {x_var:.1f}, Y方差: {y_var:.1f}")

    # 简单判定逻辑
    if click_rate > 8 and std_interval < 0.05:
        print("⚠️ 判定结果：疑似自动脚本（点击太快且过于规律）")
    elif std_interval > 0.1 and (x_var > 1000 or y_var > 1000):
        print("✅ 判定结果：更接近真人操作（随机性较高）")
    else:
        print("❓ 判定结果：无法确定（介于真人与脚本之间）")


def main():
    print(f"开始记录鼠标点击数据，持续 {record_duration} 秒...")
    listener = mouse.Listener(on_click=on_click)
    listener.start()
    Timer(record_duration, stop_listener, args=[listener]).start()
    listener.join()

    # 分析点击数据
    analyze_clicks(click_data)


if __name__ == "__main__":
    main()
