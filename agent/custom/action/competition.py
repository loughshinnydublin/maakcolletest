import json
import time
import random
from datetime import datetime

# ===============================
# 模拟 JSON 配置
# ===============================
task_config = {
    "name": "舰队自动远征",
    "entry": "MyTask3",
    "option": {
        "fleets": [
            {"id": 2, "duration": 30},   # 单位秒
            {"id": 5, "duration": 50},
            {"id": 6, "duration": 80}
        ],
        "check_interval": 5
    }
}

# ===============================
# 模拟截图检测（真实版可用 opencv）
# ===============================
def check_expedition_complete(fleet_id: int) -> bool:
    """
    模拟检测远征是否完成
    模板匹配
    """
    return random.random() < 0.7  # 70% 概率识别为完成

# ===============================
# 收取奖励
# ===============================
def collect_expedition(fleet_id: int):
    print(f"[{datetime.now().strftime('%H:%M:%S')}]  收取第 {fleet_id} 队远征奖励")

# ===============================
# 派出远征
# ===============================
def start_expedition(fleet_id: int, duration: int):
    now = time.time()
    finish_time = now + duration
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🚢 第 {fleet_id} 队开始远征（{duration}s）")
    return finish_time

# ===============================
# 主流程
# ===============================
def run_task(task_conf):
    fleets = task_conf["option"]["fleets"]
    check_interval = task_conf["option"]["check_interval"]

    # 初始化每个队伍的状态
    state = {}
    for f in fleets:
        fid = f["id"]
        dur = f["duration"]
        finish_time = start_expedition(fid, dur)
        state[fid] = {
            "duration": dur,
            "status": "running",
            "finish_time": finish_time,
            "next_check_time": finish_time,  # 默认到期再检查
        }

    print("\n=== 自动远征任务开始 ===\n")

    while True:
        now = time.time()
        for fid, info in state.items():
            # 等待到下次检测时间
            if now < info["next_check_time"]:
                remain = int(info["next_check_time"] - now)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ 第 {fid} 队剩余 {remain}s")
                continue

            # 如果时间到了，进行检测
            if info["status"] == "running" and now >= info["finish_time"]:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 检测第 {fid} 队是否远征完成...")
                if check_expedition_complete(fid):
                    collect_expedition(fid)
                    # 重新出征
                    new_finish_time = start_expedition(fid, info["duration"])
                    state[fid].update({
                        "status": "running",
                        "finish_time": new_finish_time,
                        "next_check_time": new_finish_time
                    })
                else:
                    # 没检测到完成，稍后再试
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 第 {fid} 队未检测到完成标志，{check_interval}s 后重试。")
                    state[fid]["next_check_time"] = now + check_interval

        print("------")
        time.sleep(check_interval)

# ===============================
# 主入口
# ===============================
if __name__ == "__main__":
    run_task(task_config)
