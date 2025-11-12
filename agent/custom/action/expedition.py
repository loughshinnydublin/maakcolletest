import json
import time
import random
import threading
from datetime import datetime
from .include import *




# 全局变量：控制远征线程
expedition_thread = None
expedition_stop_event = threading.Event()

@AgentServer.custom_action("AutoExpedition")
class AutoExpedition(CustomAction):
    logger.info(" AutoExpedition 类定义完成，装饰器已执行")

    """
    自定义动作：自动远征
    
    参数形式: 
    {
        "mode": "start",  // "start" 启动后台远征, "stop" 停止后台远征
        "exp1": "2队进行的远征序号",
        "exp2": "3队进行的远征序号",
        "exp3": "4队进行的远征序号",
        "background": true  // 是否在后台运行（默认true）
    }
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        logger.info(f"AutoExpedition 开始运行")
        logger.info(f"参数: {argv.custom_action_param}")

        params = json.loads(argv.custom_action_param) if argv.custom_action_param else {}
        mode = params.get("mode", "start")
        background = params.get("background", True)

        if mode == "stop":
            # 停止后台远征
            return self.stop_expedition()
        
        if background:
            # 后台模式：启动线程并立即返回
            return self.start_background_expedition(context, params)
        else:
            # 前台模式：阻塞运行
            run_task(task_config, context)
            return CustomAction.RunResult(success=True)

    def start_background_expedition(self, context: Context, params: dict) -> CustomAction.RunResult:
        """启动后台远征线程"""
        global expedition_thread, expedition_stop_event
        
        if expedition_thread and expedition_thread.is_alive():
            logger.warning("远征线程已在运行中")
            return CustomAction.RunResult(success=True)
        
        # 重置停止事件
        expedition_stop_event.clear()
        
        # 启动后台线程
        expedition_thread = threading.Thread(
            target=run_task_background,
            args=(task_config, context, expedition_stop_event),
            daemon=True,  # 守护线程，主程序退出时自动结束
            name="ExpeditionThread"
        )
        expedition_thread.start()
        
        logger.info(" 远征系统已启动（后台模式）")
        logger.info(" 其他任务可以继续执行")
        
        return CustomAction.RunResult(success=True)
    
    def stop_expedition(self) -> CustomAction.RunResult:
        """停止后台远征"""
        global expedition_thread, expedition_stop_event
        
        if not expedition_thread or not expedition_thread.is_alive():
            logger.info("远征线程未运行")
            return CustomAction.RunResult(success=True)
        
        logger.info("正在停止远征系统...")
        expedition_stop_event.set()
        
        # 等待线程结束（最多5秒）
        expedition_thread.join(timeout=5)
        
        if expedition_thread.is_alive():
            logger.warning("远征线程未能正常停止")
            return CustomAction.RunResult(success=False)
        else:
            logger.info("✅ 远征系统已停止")
            return CustomAction.RunResult(success=True)



# ===============================
# 模拟 JSON 配置
# ===============================
task_config = {
    "name": "舰队自动远征",
    "entry": "MyTask3",
    "option": {
        "fleets": [
            {"id": 2, "duration": 12},   # 单位秒
            {"id": 5, "duration": 20},
            {"id": 6, "duration": 15}
        ],
        "check_interval": 10
    }
}

# ===============================
# 模拟截图检测（真实版可用 opencv）
# ===============================
def check_expedition_complete(fleet_id: int, context: Context = None) -> bool:
    """
    模拟检测远征是否完成
    模板匹配
    """
    if context:
        # 真实检测逻辑
        try:
            detail = context.run_recognition("CheckExpeditionComplete")
            return detail and detail.box
        except Exception as e:
            logger.error(f"检测舰队{fleet_id}时出错: {e}")
            return False
    return True  # 测试模式

# ===============================
# 收取奖励
# ===============================
def collect_expedition(fleet_id: int, context: Context = None):
    logger.info(f"💰 收取第 {fleet_id} 队远征奖励")
    if context:
        try:
            context.run_task(f"CollectExpedition_{fleet_id}")
        except Exception as e:
            logger.error(f"收取舰队{fleet_id}奖励时出错: {e}")

# ===============================
# 派出远征
# ===============================
def start_expedition(fleet_id: int, duration: int, context: Context = None):
    now = time.time()
    finish_time = now + duration
    logger.info(f"🚢 第 {fleet_id} 队开始远征（{duration}s）")
    if context:
        try:
            context.run_task(f"StartExpedition_{fleet_id}")
        except Exception as e:
            logger.error(f"派出舰队{fleet_id}时出错: {e}")
    return finish_time

# ===============================
# 后台运行函数（支持停止信号）
# ===============================
def run_task_background(task_conf, context: Context, stop_event: threading.Event):
    """
    后台运行远征任务
    
    Args:
        task_conf: 任务配置
        context: MAA Context
        stop_event: 停止事件信号
    """
    logger.info("="*50)
    logger.info("🚀 远征系统后台线程启动")
    logger.info("="*50)
    
    fleets = task_conf["option"]["fleets"]
    check_interval = task_conf["option"]["check_interval"]

    # 初始化每个队伍的状态
    state = {}
    for f in fleets:
        fid = f["id"]
        dur = f["duration"]
        finish_time = start_expedition(fid, dur, context)
        state[fid] = {
            "duration": dur,
            "status": "running",
            "finish_time": finish_time,
            "next_check_time": finish_time,
        }

    logger.info("=== 自动远征任务开始（后台模式）===")
    
    while not stop_event.is_set():
        now = time.time()
        
        for fid, info in state.items():
            # 检查停止信号
            if stop_event.is_set():
                break
            
            # 等待到下次检测时间
            if now < info["next_check_time"]:
                remain = int(info["next_check_time"] - now)
                logger.debug(f"⏳ 第 {fid} 队剩余 {remain}s")
                continue

            # 如果时间到了，进行检测
            if info["status"] == "running" and now >= info["finish_time"]:
                logger.info(f"� 检测第 {fid} 队是否远征完成...")
                
                if check_expedition_complete(fid, context):
                    collect_expedition(fid, context)
                    # 重新出征
                    new_finish_time = start_expedition(fid, info["duration"], context)
                    state[fid].update({
                        "status": "running",
                        "finish_time": new_finish_time,
                        "next_check_time": new_finish_time
                    })
                else:
                    # 没检测到完成，稍后再试
                    logger.warning(f"❌ 第 {fid} 队未检测到完成标志，{check_interval}s 后重试。")
                    state[fid]["next_check_time"] = now + check_interval

        # 短暂休眠，避免CPU占用过高
        time.sleep(1)
    
    logger.info("=== 自动远征任务结束（后台线程停止）===")

# ===============================
# 前台运行函数（原版，阻塞式）
# ===============================
def run_task(task_conf, context: Context = None):
    """前台运行（阻塞式）- 兼容原版"""
    fleets = task_conf["option"]["fleets"]
    check_interval = task_conf["option"]["check_interval"]
    max_iterations = task_conf["option"].get("max_iterations", 4)

    # 初始化每个队伍的状态
    state = {}
    for f in fleets:
        fid = f["id"]
        dur = f["duration"]
        finish_time = start_expedition(fid, dur, context)
        state[fid] = {
            "duration": dur,
            "status": "running",
            "finish_time": finish_time,
            "next_check_time": finish_time,
        }

    logger.info("=== 自动远征任务开始（前台模式）===")
    
    iteration_count = 0
    while iteration_count < max_iterations:
        iteration_count += 1
        logger.info(f"{iteration_count}/{max_iterations} 次检测循环")
        
        now = time.time()
        for fid, info in state.items():
            # 等待到下次检测时间
            if now < info["next_check_time"]:
                remain = int(info["next_check_time"] - now)
                logger.info(f"⏳ 第 {fid} 队剩余 {remain}s")
                continue

            # 如果时间到了，进行检测
            if info["status"] == "running" and now >= info["finish_time"]:
                logger.info(f"🔍 检测第 {fid} 队是否远征完成...")
                
                if check_expedition_complete(fid, context):
                    collect_expedition(fid, context)
                    # 重新出征
                    new_finish_time = start_expedition(fid, info["duration"], context)
                    state[fid].update({
                        "status": "running",
                        "finish_time": new_finish_time,
                        "next_check_time": new_finish_time
                    })
                else:
                    # 没检测到完成，稍后再试
                    logger.warning(f"❌ 第 {fid} 队未检测到完成标志，{check_interval}s 后重试。")
                    state[fid]["next_check_time"] = now + check_interval

        logger.info("------")
        time.sleep(check_interval)
    
    logger.info("=== 自动远征任务结束 ===")

# ===============================
# 主入口
# ===============================
# if __name__ == "__main__":
#     run_task(task_config)
