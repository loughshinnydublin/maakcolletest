"""
mouse_realness_detector.py

功能：
1) 监听并记录鼠标全局移动轨迹 (x, y, timestamp)
2) 导出 CSV（可选）
3) 基于多项启发式指标计算“真人化分数”（0..1），并输出判定

依赖：
pip install pynput numpy scipy pandas
（pandas/scipy 可选，用于导出/高级统计；脚本会在缺少时回退）

运行：
python mouse_realness_detector.py
按 Ctrl+C 或 Esc 停止记录（可在代码中修改停止键/时长）
"""

import time
import math
import threading
import sys
from collections import deque

try:
    from pynput import mouse, keyboard
except Exception as e:
    print("需要安装 pynput：pip install pynput")
    raise

# 可选依赖
try:
    import numpy as np
except Exception:
    print("建议安装 numpy：pip install numpy")
    np = None

try:
    import pandas as pd
except Exception:
    pd = None

# ------------- 配置 -------------
MAX_RECORD_SECONDS = None   # None 表示手动停止；否则录制指定秒数后自动停止
STOP_KEY = keyboard.Key.esc  # 按 Esc 停止（也可以改为 None）
SAVE_CSV = True             # 是否保存轨迹到 CSV
CSV_PATH = "mouse_trace.csv"
RESULT_DETAIL_CSV = "mouse_metrics.csv"  # 可选详细特征导出
SPEED_LOW_THRESHOLD = 5.0   # px/s 以下视作静止（用于检测停顿）
# --------------------------------

class MouseRecorder:
    def __init__(self):
        self.points = []  # (t, x, y)
        self._lock = threading.Lock()
        self._running = False
        self._listener = None
        self._kbd_listener = None

    def _on_move(self, x, y):
        with self._lock:
            self.points.append((time.time(), float(x), float(y)))

    def _on_click(self, x, y, button, pressed):
        # 也记录点击时间点（方便后续分析）
        with self._lock:
            self.points.append((time.time(), float(x), float(y), 'click', str(button), pressed))

    def _on_scroll(self, x, y, dx, dy):
        with self._lock:
            self.points.append((time.time(), float(x), float(y), 'scroll', dx, dy))

    def start(self):
        self._running = True
        # 使用 pynput mouse listener
        self._listener = mouse.Listener(on_move=self._on_move, on_click=self._on_click, on_scroll=self._on_scroll)
        self._listener.start()
        # keyboard listener to stop
        if STOP_KEY is not None:
            def on_press(key):
                if key == STOP_KEY:
                    print("检测到停止键，停止记录。")
                    self.stop()
                    return False
            self._kbd_listener = keyboard.Listener(on_press=on_press)
            self._kbd_listener.start()
        print("开始记录鼠标轨迹，按 Esc 停止（或 Ctrl+C）...")

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
        if self._kbd_listener:
            self._kbd_listener.stop()

    def get_points(self):
        with self._lock:
            # 规范化输出：只保留 (t,x,y) 的连续点（即跳过 click/scroll 记录）
            pts = []
            for item in self.points:
                if len(item) >= 3 and isinstance(item[0], float):
                    # If extra fields exist (click/scroll), the first 3 are t,x,y
                    pts.append((item[0], float(item[1]), float(item[2])))
            return pts

# -------- 特征计算与判定逻辑 --------
def compute_metrics(points):
    """
    输入：points = [(t0,x0,y0), (t1,x1,y1), ...] 按时间排序
    输出：metrics dict
    """
    if np is None:
        raise RuntimeError("本函数依赖 numpy，建议安装：pip install numpy")

    if len(points) < 3:
        return {"error": "数据点太少，至少需要3个点"}

    arr = np.array(points)  # shape (n,3)
    t = arr[:,0]
    x = arr[:,1]
    y = arr[:,2]

    dt = np.diff(t)
    dx = np.diff(x)
    dy = np.diff(y)
    dist = np.hypot(dx, dy)             # 每段距离（px）
    speed = dist / np.maximum(dt, 1e-6) # px/s
    # 常规统计
    total_time = t[-1] - t[0]
    total_path = dist.sum()
    displacement = math.hypot(x[-1] - x[0], y[-1] - y[0])
    straightness = displacement / (total_path + 1e-9)  # 越接近1越直线

    # 加速度与 jerk
    # acceleration: change of speed / dt[1:]
    acc = np.diff(speed) / np.maximum(dt[1:], 1e-6)
    # jerk: change of acc / dt[2:]
    if len(acc) >= 2:
        jerk = np.diff(acc) / np.maximum(dt[2:], 1e-6)
    else:
        jerk = np.array([])

    # 方向角与方向变化
    angles = np.arctan2(dy, dx)  # [-pi, pi]
    ang_diff = np.diff(angles)
    # 规范化角差到 [-pi, pi]
    ang_diff = (ang_diff + np.pi) % (2*np.pi) - np.pi
    ang_change_mag = np.abs(ang_diff)

    # 暂停段（速度小于阈值认为静止）
    pauses = speed < SPEED_LOW_THRESHOLD
    # 连续静止段统计：计算静止段总时长和数量
    pause_segments = 0
    pause_total_time = 0.0
    i = 0
    while i < len(pauses):
        if pauses[i]:
            j = i
            while j < len(pauses) and pauses[j]:
                j += 1
            # segment spans from index i to j (in speed indices),
            # corresponding time length approx t[j] - t[i]
            seg_time = t[i+1] - t[i] if i+1 < len(t) else 0.0
            pause_segments += 1
            # sum dt across this segment
            pause_total_time += dt[i:j].sum()
            i = j
        else:
            i += 1

    # 速度分布熵（离散化速度，测不规则性）
    hist, edges = np.histogram(speed, bins=16, density=True)
    # 熵
    hist = hist + 1e-12
    entropy = -np.sum(hist * np.log(hist))

    metrics = {
        "num_points": len(points),
        "total_time_s": float(total_time),
        "total_path_px": float(total_path),
        "displacement_px": float(displacement),
        "straightness": float(straightness),
        "mean_speed": float(np.mean(speed)),
        "median_speed": float(np.median(speed)),
        "std_speed": float(np.std(speed)),
        "max_speed": float(np.max(speed)),
        "mean_acc": float(np.mean(acc)) if len(acc) else 0.0,
        "std_acc": float(np.std(acc)) if len(acc) else 0.0,
        "mean_jerk": float(np.mean(jerk)) if len(jerk) else 0.0,
        "std_jerk": float(np.std(jerk)) if len(jerk) else 0.0,
        "mean_angle_change": float(np.mean(ang_change_mag)) if len(ang_change_mag) else 0.0,
        "std_angle_change": float(np.std(ang_change_mag)) if len(ang_change_mag) else 0.0,
        "pause_segments": int(pause_segments),
        "pause_total_time_s": float(pause_total_time),
        "speed_entropy": float(entropy),
        "avg_sample_dt": float(np.mean(dt)),
        "min_dt": float(np.min(dt)),
        "max_dt": float(np.max(dt)),
    }
    # 为后续分析返回一些数组（不包含在 metrics）
    extra = {
        "dt": dt, "dist": dist, "speed": speed, "acc": acc, "jerk": jerk,
        "angles": angles, "ang_change_mag": ang_change_mag
    }
    return metrics, extra

def score_human_likeness(metrics):
    """
    将计算得到的 metrics 转换为 0..1 的真人化评分（越高越像真人）。
    基于若干启发式规则与阈值。可根据需要调整权重。
    """
    # 如果 metrics 是 error dict
    if "error" in metrics:
        return {"score": 0.0, "reason": metrics["error"]}

    # 提取常用量
    mean_speed = metrics["mean_speed"]
    std_speed = metrics["std_speed"]
    straightness = metrics["straightness"]
    pause_segments = metrics["pause_segments"]
    pause_total = metrics["pause_total_time_s"]
    entropy = metrics["speed_entropy"]
    mean_acc = abs(metrics["mean_acc"])
    std_jerk = metrics["std_jerk"]

    # 各项评分 0..1（1 表示更像真人）
    # 1) 速度范围：人类移动通常不完全天然太快或太慢（取经验区间）
    #    对 mean_speed 做类似高斯评分
    def gaussian_score(x, mu, sigma):
        return math.exp(-0.5 * ((x - mu) / (sigma + 1e-9))**2)

    speed_score = gaussian_score(mean_speed, mu=400.0, sigma=700.0)  # px/s，宽容
    # 2) 速度抖动（std_speed）越大越像人（因为脚本常匀速）
    std_speed_score = min(std_speed / (mean_speed + 1e-9), 1.0) if mean_speed>1 else 0.0

    # 3) 轨迹直线度：极端直线（>=0.98）可能是脚本单直线；但人也可能直走，取中间偏低给分
    straightness_score = 1.0 - abs(straightness - 0.6)  # 假设人多为曲线路径，越接近0.6得分高
    straightness_score = max(0.0, min(1.0, straightness_score))

    # 4) 暂停特征：人会有零散停顿，若完全无停顿也可疑（例如连续匀速）
    pause_score = 0.5 + min(1.0, pause_segments / 5.0) * 0.5  # 有一定停顿更像人

    # 5) 速度熵：熵越高表示速度分布更丰富，越像人
    # 先将 entropy 归一化（在常见范围 0.5..2.5）
    entropy_norm = (entropy - 0.3) / (2.0)  # 粗归一化
    entropy_score = max(0.0, min(1.0, entropy_norm))

    # 6) 加减速/jerk：人会有显著 jerk，值越大越像人
    jerk_score = math.tanh(std_jerk / 1000.0)  # 缩放并压缩

    # 合并权重（可调）
    w = {
        "speed": 0.15,
        "std_speed": 0.18,
        "straightness": 0.12,
        "pause": 0.15,
        "entropy": 0.15,
        "jerk": 0.15,
        "extra": 0.1
    }
    # Normalize weights to 1
    total_w = sum(w.values())
    for k in w: w[k] /= total_w

    final_score = (
        w["speed"] * speed_score +
        w["std_speed"] * std_speed_score +
        w["straightness"] * straightness_score +
        w["pause"] * pause_score +
        w["entropy"] * entropy_score +
        w["jerk"] * jerk_score
    )

    # clamp
    final_score = max(0.0, min(1.0, final_score))

    # rule-based hard checks (如果有强烈异常则降低分)
    reasons = []
    if mean_speed > 10000 and final_score > 0.3:
        final_score *= 0.3
        reasons.append("平均速度异常高，可能为脚本")
    if straightness > 0.995:
        final_score *= 0.4
        reasons.append("轨迹高度直线化，疑似脚本")
    if metrics["num_points"] < 5:
        final_score *= 0.6
        reasons.append("记录点数太少，判定不确定")

    return {
        "score": final_score,
        "component_scores": {
            "speed_score": speed_score,
            "std_speed_score": std_speed_score,
            "straightness_score": straightness_score,
            "pause_score": pause_score,
            "entropy_score": entropy_score,
            "jerk_score": jerk_score
        },
        "reasons": reasons
    }

# ---------- 主流程 -----------
def main():
    rec = MouseRecorder()
    rec.start()

    start_time = time.time()
    try:
        if MAX_RECORD_SECONDS is not None:
            # 自动停止路径
            while time.time() - start_time < MAX_RECORD_SECONDS and rec._running:
                time.sleep(0.1)
            rec.stop()
        else:
            # 手动停止（通过 Esc 或 Ctrl+C）
            while rec._running:
                time.sleep(0.2)
    except KeyboardInterrupt:
        print("KeyboardInterrupt, stopping...")
        rec.stop()

    pts = rec.get_points()
    if len(pts) == 0:
        print("未记录到点，退出。")
        sys.exit(0)

    # 导出原始轨迹 CSV（可选）
    if SAVE_CSV and pd is not None:
        df = pd.DataFrame(pts, columns=["t", "x", "y"])
        df.to_csv(CSV_PATH, index=False)
        print(f"已保存轨迹 CSV -> {CSV_PATH}")
    elif SAVE_CSV:
        # 无 pandas，手动写
        with open(CSV_PATH, "w", encoding="utf-8") as f:
            f.write("t,x,y\n")
            for a,b,c in pts:
                f.write(f"{a},{b},{c}\n")
        print(f"(无 pandas) 已保存轨迹 CSV -> {CSV_PATH}")

    # 计算特征
    try:
        metrics, extra = compute_metrics(pts)
    except Exception as e:
        print("计算特征失败：", e)
        sys.exit(1)

    # 导出详细特征（速度序列等）
    if pd is not None:
        # 构造 df
        df_detail = pd.DataFrame({
            "dt": np.concatenate(([np.nan], extra["dt"])),
            "dist": np.concatenate(([np.nan], extra["dist"])),
            "speed": np.concatenate(([np.nan], extra["speed"])),
        })
        df_detail.to_csv(RESULT_DETAIL_CSV, index=False)
        print(f"已保存详细特征 -> {RESULT_DETAIL_CSV}")

    # 评分
    result = score_human_likeness(metrics if isinstance(metrics, dict) else metrics[0])
    score = result["score"] if isinstance(result, dict) else 0.0

    # 输出结果
    print("\n--- 分析结果 ---")
    for k, v in metrics.items():
        print(f"{k}: {v}")
    print("\n综合真人化评分 (0..1): {:.3f}".format(score))
    if "component_scores" in result:
        print("分项：")
        for k,v in result["component_scores"].items():
            print(f"  {k}: {v:.3f}")
    if result.get("reasons"):
        print("警告/原因：")
        for r in result["reasons"]:
            print(" -", r)

    verdict = "真人" if score >= 0.6 else ("可能真人" if score >= 0.4 else "疑似脚本/自动化")
    print("最终判定：", verdict)

if __name__ == "__main__":
    main()
