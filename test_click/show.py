import pandas as pd
import matplotlib.pyplot as plt

# 读取数据
df = pd.read_csv("mouse_trace.csv")

# 绘制轨迹
plt.plot(df["x"], df["y"], marker="o", label="Distance")
plt.title("Mouse Movement Trajectory")
plt.xlabel("Time (s)")
plt.ylabel("Distance (px)")
plt.gca().invert_yaxis()  # GUI 坐标系原点在左上角
plt.show()
