"""
组合任务：远征 + 5-2出击并发执行
使用线程和事件进行协调
"""

import json
import time
import threading
from datetime import datetime
from .include import *


# ===============================
# 全局控制变量
# ===============================
expedition_thread = None
combat_thread = None
stop_event = threading.Event()  # 停止所有任务
combat_pause_event = threading.Event()  # 暂停5-2出击
combat_pause_event.set()  # 初始状态：允许出击


@AgentServer.custom_action("AutoCombinedTasks")
class AutoCombinedTasks(CustomAction):
    """
    自定义动作：远征 + 5-2出击 组合任务
    
    参数形式:
    {
        "mode": "start",  // "start" 启动, "stop" 停止
        "expedition_config": {
            "fleets": [
                {"id": 2, "duration": 720},
                {"id": 5, "duration": 1200}
            ],
            "check_interval": 10
        },
        "combat_config": {
            "map": "5-2",
            "interval": 5
        }
    }
    """
    
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        
        logger.info("AutoCombinedTasks 开始运行")
        logger.info(f"参数: {argv.custom_action_param}")
        
        params = json.loads(argv.custom_action_param) if argv.custom_action_param else {}
        mode = params.get("mode", "start")
        
        if mode == "stop":
            return self.stop_all_tasks()
        else:
            return self.start_all_tasks(context, params)
    
    def start_all_tasks(self, context: Context, params: dict) -> CustomAction.RunResult:
        """启动所有任务"""
        global expedition_thread, combat_thread, stop_event, combat_pause_event
        
        if expedition_thread and expedition_thread.is_alive():
            logger.warning("任务已在运行中")
            return CustomAction.RunResult(success=True)
        
        # 重置事件
        stop_event.clear()
        combat_pause_event.set()  # 允许出击
        
        # 获取配置
        exp_config = params.get("expedition_config", default_expedition_config)
        combat_config = params.get("combat_config", default_combat_config)
        
        # 启动远征线程
        expedition_thread = threading.Thread(
            target=expedition_loop,
            args=(context, exp_config, stop_event, combat_pause_event),
            daemon=True,
            name="ExpeditionThread"
        )
        
        # 启动5-2出击线程
        combat_thread = threading.Thread(
            target=combat_loop,
            args=(context, combat_config, stop_event, combat_pause_event),
            daemon=True,
            name="CombatThread"
        )
        
        expedition_thread.start()
        combat_thread.start()
        
        logger.info("="*60)
        logger.info(" 组合任务已启动")
        logger.info("  - 远征线程：后台运行")
        logger.info("  - 5-2出击线程：后台运行")
        logger.info("  - 远征收取时会自动暂停出击")
        logger.info("="*60)
        
        return CustomAction.RunResult(success=True)
    
    def stop_all_tasks(self) -> CustomAction.RunResult:
        """停止所有任务"""
        global expedition_thread, combat_thread, stop_event
        
        logger.info("正在停止所有任务...")
        stop_event.set()
        
        # 等待线程结束
        threads = [
            (expedition_thread, "远征线程"),
            (combat_thread, "5-2出击线程")
        ]
        
        for thread, name in threads:
            if thread and thread.is_alive():
                thread.join(timeout=5)
                if thread.is_alive():
                    logger.warning(f"{name}未能正常停止")
                else:
                    logger.info(f" {name}已停止")
        
        return CustomAction.RunResult(success=True)


# ===============================
# 默认配置
# ===============================
default_expedition_config = {
    "fleets": [
        {"id": 2, "duration": 720},   # 12分钟
        {"id": 5, "duration": 1200},  # 20分钟
        {"id": 6, "duration": 900}    # 15分钟
    ],
    "check_interval": 10
}

default_combat_config = {
    "map": "5-2",
    "interval": 5
}


# ===============================
# 远征循环
# ===============================
def expedition_loop(
    context: Context, 
    config: dict, 
    stop_event: threading.Event,
    combat_pause_event: threading.Event
):
    """
    远征主循环
    
    Args:
        context: MAA Context
        config: 远征配置
        stop_event: 停止信号
        combat_pause_event: 5-2出击暂停信号（用于暂停出击）
    """
    logger.info("[远征] 线程启动")
    
    fleets = config["fleets"]
    check_interval = config["check_interval"]
    
    # 初始化舰队状态
    state = {}
    for f in fleets:
        fid = f["id"]
        dur = f["duration"]
        
        # 初次派出需要暂停5-2
        logger.info(f"[远征] 初始化第{fid}队...")
        pause_combat_for_expedition(combat_pause_event, f"初始派出第{fid}队")
        
        finish_time = start_expedition(fid, dur, context)
        state[fid] = {
            "duration": dur,
            "status": "running",
            "finish_time": finish_time,
            "next_check_time": finish_time
        }
        
        resume_combat(combat_pause_event, f"第{fid}队已派出")
        time.sleep(0.5)  # 短暂延迟，避免频繁暂停
    
    logger.info("[远征] 所有舰队初始化完成")
    
    # 主循环
    while not stop_event.is_set():
        now = time.time()
        
        for fid, info in state.items():
            if stop_event.is_set():
                break
            
            # 等待到下次检测时间
            if now < info["next_check_time"]:
                continue
            
            # 检测远征是否完成
            if info["status"] == "running" and now >= info["finish_time"]:
                logger.info(f"[远征] 🔍 检测第{fid}队...")
                
                if check_expedition_complete(fid, context):
                    # 远征完成，暂停5-2出击
                    pause_combat_for_expedition(
                        combat_pause_event, 
                        f"第{fid}队完成，开始收取和派出"
                    )
                    
                    # 收取奖励
                    collect_expedition(fid, context)
                    time.sleep(1)
                    
                    # 重新派出
                    new_finish_time = start_expedition(fid, info["duration"], context)
                    state[fid].update({
                        "status": "running",
                        "finish_time": new_finish_time,
                        "next_check_time": new_finish_time
                    })
                    time.sleep(1)
                    
                    # 恢复5-2出击
                    resume_combat(combat_pause_event, f"第{fid}队已重新派出")
                    
                else:
                    # 未完成，稍后重试
                    logger.warning(f"[远征] ❌ 第{fid}队未完成，{check_interval}秒后重试")
                    state[fid]["next_check_time"] = now + check_interval
        
        # 短暂休眠
        time.sleep(1)
    
    logger.info("[远征] 线程结束")


# ===============================
# 5-2出击循环
# ===============================
def combat_loop(
    context: Context,
    config: dict,
    stop_event: threading.Event,
    combat_pause_event: threading.Event
):
    """
    5-2出击主循环
    
    Args:
        context: MAA Context
        config: 出击配置
        stop_event: 停止信号
        combat_pause_event: 暂停信号（远征收取时会清除此事件）
    """
    logger.info("[5-2] 线程启动")
    
    map_name = config["map"]
    interval = config["interval"]
    
    while not stop_event.is_set():
        # 等待暂停事件被设置（允许出击）
        combat_pause_event.wait()
        
        # 再次检查是否需要停止
        if stop_event.is_set():
            break
        
        # 执行一次5-2出击
        logger.info(f"[5-2]  开始出击 {map_name}")
        
        try:
            # 执行出击任务
            run_combat_once(context, map_name)
            logger.info(f"[5-2]  出击完成")
        except Exception as e:
            logger.error(f"[5-2]  出击出错: {e}")
        
        # 等待一段时间再继续
        for _ in range(interval):
            if stop_event.is_set() or not combat_pause_event.is_set():
                break
            time.sleep(1)
    
    logger.info("[5-2] 线程结束")


# ===============================
# 协调函数
# ===============================
def pause_combat_for_expedition(combat_pause_event: threading.Event, reason: str):
    """暂停5-2出击（用于远征收取和派出）"""
    logger.info(f"[协调]   暂停5-2出击 - {reason}")
    combat_pause_event.clear()  # 清除事件，阻塞5-2线程
    time.sleep(0.5)  # 给5-2线程一点时间停下来

def resume_combat(combat_pause_event: threading.Event, reason: str):
    """恢复5-2出击"""
    logger.info(f"[协调]   恢复5-2出击 - {reason}")
    combat_pause_event.set()  # 设置事件，允许5-2继续


# ===============================
# 远征相关函数
# ===============================
def check_expedition_complete(fleet_id: int, context: Context) -> bool:
    """检测远征是否完成"""
    try:
        detail = context.run_recognition(f"CheckExpeditionComplete_{fleet_id}")
        return detail and detail.box
    except Exception as e:
        logger.error(f"[远征] 检测第{fleet_id}队时出错: {e}")
        return False

def collect_expedition(fleet_id: int, context: Context):
    """收取远征奖励"""
    logger.info(f"[远征]  收取第{fleet_id}队奖励")
    try:
        context.run_task(f"CollectExpedition_{fleet_id}")
    except Exception as e:
        logger.error(f"[远征] 收取第{fleet_id}队奖励时出错: {e}")

def start_expedition(fleet_id: int, duration: int, context: Context) -> float:
    """派出远征"""
    now = time.time()
    finish_time = now + duration
    logger.info(f"[远征]  第{fleet_id}队开始远征（{duration}秒 = {duration//60}分钟）")
    try:
        context.run_task(f"StartExpedition_{fleet_id}")
    except Exception as e:
        logger.error(f"[远征] 派出第{fleet_id}队时出错: {e}")
    return finish_time


# ===============================
# 5-2出击相关函数
# ===============================
def run_combat_once(context: Context, map_name: str):
    """执行一次出击"""
    try:
        # 执行出击流程
        context.run_task(f"Combat_{map_name}")
    except Exception as e:
        logger.error(f"[5-2] 出击{map_name}时出错: {e}")
        raise


# ===============================
# 主入口（测试用）
# ===============================
if __name__ == "__main__":
    # 测试代码
    print("组合任务系统已加载")
    print("在 MAA 中使用 AutoCombinedTasks 自定义动作")
