"""
优化版自动远征程序 - 独立计时器方案
每个舰队使用独立的检测间隔，智能减少检测次数
"""

import json
import time
import heapq
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from utils.logger import custom_logger as logger

# ===============================
# 配置
# ===============================
task_config = {
    "name": "舰队自动远征 - 优化版",
    "entry": "MyTask3",
    "option": {
        "fleets": [
            {"id": 2, "duration": 720, "check_strategy": "exact"},    # 12分钟
            {"id": 5, "duration": 1200, "check_strategy": "early"},   # 20分钟
            {"id": 6, "duration": 900, "check_strategy": "adaptive"}  # 15分钟
        ],
        # 全局保底检测间隔（防止遗漏）
        "global_check_interval": 60,
        # 检测策略配置
        "strategies": {
            "exact": {
                "desc": "精确模式：仅在预计完成时检测",
                "check_before": 0,      # 提前0秒检测
                "retry_interval": 10    # 如未完成，10秒后重试
            },
            "early": {
                "desc": "提前模式：提前检测，适合短期远征",
                "check_before": 5,      # 提前5秒检测
                "retry_interval": 10    # 如未完成，10秒后重试
            },
            "adaptive": {
                "desc": "自适应模式：根据时长动态调整",
                "check_before_ratio": 0.02,  # 提前2%时长检测
                "retry_interval": 10
            }
        },
        # 舰队区域定义 (x, y, width, height)
        "fleet_regions": {
            2: {"x": 100, "y": 200, "width": 300, "height": 150, "name": "第2队区域"},
            5: {"x": 100, "y": 400, "width": 300, "height": 150, "name": "第5队区域"},
            6: {"x": 100, "y": 600, "width": 300, "height": 150, "name": "第6队区域"}
        },
        # 识别配置
        "recognition": {
            "complete_task": "CheckExpeditionComplete",  # 检测完成的识别任务
            "threshold": 0.8  # 识别阈值
        }
    }
}

# ===============================
# 真实检测函数 - 基于区域的图像识别
# ===============================
def check_expedition_complete(fleet_id: int, context: Optional[Context] = None) -> bool:
    """
    检测指定舰队的远征是否完成
    
    Args:
        fleet_id: 舰队ID
        context: MAA Context对象，如果为None则返回模拟结果（用于测试）
    
    Returns:
        True: 远征已完成
        False: 远征未完成
    """
    if context is None:
        # 测试模式：模拟检测
        logger.warning(f"舰队{fleet_id}使用模拟检测（无Context）")
        return True
    
    try:
        # 获取舰队区域配置
        fleet_region = task_config["option"]["fleet_regions"].get(fleet_id)
        if not fleet_region:
            logger.error(f"未找到舰队{fleet_id}的区域配置")
            return False
        
        # 设置识别区域
        rec_task = task_config["option"]["recognition"]["complete_task"]
        threshold = task_config["option"]["recognition"]["threshold"]
        
        # 构造识别参数
        rec_param = {
            "recognition": rec_task,
            "roi": [
                fleet_region["x"],
                fleet_region["y"],
                fleet_region["width"],
                fleet_region["height"]
            ],
            "threshold": threshold
        }
        
        logger.info(f"检测舰队{fleet_id}区域: {fleet_region['name']}")
        
        # 执行识别
        detail = context.run_recognition(
            entry=rec_task,
            pipeline_override=rec_param
        )
        
        # 判断识别结果
        if detail and detail.box:
            logger.info(f" 舰队{fleet_id}远征完成 (置信度: {detail.score:.2f})")
            return True
        else:
            logger.info(f" 舰队{fleet_id}远征未完成")
            return False
            
    except Exception as e:
        logger.error(f"检测舰队{fleet_id}时出错: {e}", exc_info=True)
        return False

# ===============================
# 收取与派出
# ===============================
def collect_expedition(fleet_id: int, context: Optional[Context] = None):
    """收取远征奖励"""
    logger.info(f" 收取第 {fleet_id} 队远征奖励")
    
    if context:
        # 实际执行：运行收取流程
        try:
            context.run_task(f"CollectExpedition_{fleet_id}")
        except Exception as e:
            logger.error(f"收取舰队{fleet_id}奖励时出错: {e}", exc_info=True)

def start_expedition(fleet_id: int, duration: int, context: Optional[Context] = None) -> float:
    """派出远征"""
    now = time.time()
    finish_time = now + duration
    logger.info(f"🚢 第 {fleet_id} 队开始远征（{duration}s = {duration//60}分钟）")
    
    if context:
        # 实际执行：运行派出流程
        try:
            context.run_task(f"StartExpedition_{fleet_id}")
        except Exception as e:
            logger.error(f"派出舰队{fleet_id}时出错: {e}", exc_info=True)
    
    return finish_time

# ===============================
# 优化版：使用优先队列（堆）管理检测时间
# ===============================
class FleetScheduler:
    """舰队调度器 - 使用最小堆管理检测时间点"""
    
    def __init__(self, config: dict, context: Optional[Context] = None):
        self.config = config
        self.context = context  # MAA Context 对象
        self.fleets = config["option"]["fleets"]
        self.strategies = config["option"]["strategies"]
        self.global_interval = config["option"]["global_check_interval"]
        
        # 优先队列: (检测时间, 舰队ID, 检测类型)
        self.check_queue: List[Tuple[float, int, str]] = []
        
        # 舰队状态
        self.fleet_states: Dict[int, dict] = {}
        
        # 统计信息
        self.stats = {
            "total_checks": 0,
            "successful_collections": 0,
            "failed_checks": 0
        }
        
        # 模式标志
        self.is_test_mode = context is None
        if self.is_test_mode:
            logger.warning("调度器运行在测试模式（无Context）")
    
    def get_check_time(self, fleet_id: int, finish_time: float, strategy_name: str) -> float:
        """根据策略计算检测时间"""
        strategy = self.strategies.get(strategy_name, self.strategies["exact"])
        duration = finish_time - time.time()
        
        if strategy_name == "exact":
            # 精确模式：在完成时间检测
            return finish_time - strategy["check_before"]
        
        elif strategy_name == "early":
            # 提前模式：提前固定秒数
            return finish_time - strategy["check_before"]
        
        elif strategy_name == "adaptive":
            # 自适应模式：根据总时长的比例提前
            check_before = duration * strategy["check_before_ratio"]
            return finish_time - check_before
        
        return finish_time
    
    def initialize_fleets(self):
        """初始化所有舰队"""
        logger.info("=== 初始化舰队 ===")
        
        for fleet_cfg in self.fleets:
            fleet_id = fleet_cfg["id"]
            duration = fleet_cfg["duration"]
            strategy = fleet_cfg.get("check_strategy", "exact")
            
            # 派出远征
            finish_time = start_expedition(fleet_id, duration, self.context)
            
            # 计算首次检测时间
            check_time = self.get_check_time(fleet_id, finish_time, strategy)
            
            # 保存状态
            self.fleet_states[fleet_id] = {
                "duration": duration,
                "strategy": strategy,
                "finish_time": finish_time,
                "status": "running",
                "check_count": 0
            }
            
            # 加入检测队列
            heapq.heappush(self.check_queue, (check_time, fleet_id, "scheduled"))
            
            remain = int(check_time - time.time())
            logger.info(f"📋 第 {fleet_id} 队 [{strategy}模式] 将在 {remain}s 后检测")
        
        logger.info("=== 舰队初始化完成 ===")
    
    def process_check(self, fleet_id: int, check_type: str):
        """处理检测"""
        state = self.fleet_states[fleet_id]
        strategy = self.strategies[state["strategy"]]
        now = time.time()
        
        state["check_count"] += 1
        self.stats["total_checks"] += 1
        
        # 显示检测信息
        time_to_finish = int(state["finish_time"] - now)
        logger.info(f"🔍 检测第 {fleet_id} 队 [{check_type}] (距预计完成: {time_to_finish}s)")
        
        # 检测是否完成（传入context）
        if now >= state["finish_time"] and check_expedition_complete(fleet_id, self.context):
            # 远征完成
            self.stats["successful_collections"] += 1
            collect_expedition(fleet_id, self.context)
            
            # 重新派出
            new_finish_time = start_expedition(fleet_id, state["duration"], self.context)
            state["finish_time"] = new_finish_time
            state["check_count"] = 0
            
            # 安排下次检测
            next_check = self.get_check_time(fleet_id, new_finish_time, state["strategy"])
            heapq.heappush(self.check_queue, (next_check, fleet_id, "scheduled"))
            
            remain = int(next_check - time.time())
            logger.info(f"✅ 已重新派出，下次检测: {remain}s 后")
        
        else:
            # 未完成，安排重试
            self.stats["failed_checks"] += 1
            retry_interval = strategy.get("retry_interval", 10)
            retry_time = now + retry_interval
            heapq.heappush(self.check_queue, (retry_time, fleet_id, "retry"))
            
            logger.info(f"⏳ 未完成，{retry_interval}s 后重试")
    
    def run(self, max_iterations: int = None):
        """运行调度器"""
        self.initialize_fleets()
        
        iteration = 0
        logger.info("=== 开始自动远征循环 ===")
        
        while True:
            if max_iterations and iteration >= max_iterations:
                break
            
            # 获取下一个检测时间
            if not self.check_queue:
                logger.warning("⚠️ 检测队列为空，退出")
                break
            
            next_check_time, fleet_id, check_type = heapq.heappop(self.check_queue)
            
            # 等待到检测时间
            now = time.time()
            wait_time = next_check_time - now
            
            if wait_time > 0:
                logger.info(f"💤 等待 {int(wait_time)}s 直到下次检测...")
                time.sleep(wait_time)
            
            # 执行检测
            self.process_check(fleet_id, check_type)
            
            logger.info("-" * 60)
            iteration += 1
        
        # 显示统计
        self.show_statistics()
    
    def show_statistics(self):
        """显示统计信息"""
        print("\n" + "=" * 60)
        print("📊 统计信息")
        print("=" * 60)
        print(f"总检测次数: {self.stats['total_checks']}")
        print(f"成功收取次数: {self.stats['successful_collections']}")
        print(f"失败检测次数: {self.stats['failed_checks']}")
        print(f"平均每次收取检测次数: {self.stats['total_checks'] / max(1, self.stats['successful_collections']):.2f}")
        
        print("\n各舰队检测次数:")
        for fleet_id, state in self.fleet_states.items():
            print(f"  舰队 {fleet_id}: {state['check_count']} 次")
        print("=" * 60)

# ===============================
# MAA 自定义动作包装器
# ===============================
@AgentServer.custom_action("AutoExpeditionOptimized")
class AutoExpeditionOptimized(CustomAction):
    """
    优化版自动远征 - MAA 自定义动作
    
    参数格式:
    {
        "fleets": [
            {"id": 2, "duration": 720, "check_strategy": "exact"},
            {"id": 5, "duration": 1200, "check_strategy": "early"}
        ],
        "max_iterations": 100  // 可选，限制最大迭代次数
    }
    """
    
    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:
        
        logger.info("=" * 70)
        logger.info("启动优化版自动远征系统")
        logger.info("=" * 70)
        
        try:
            # 解析参数
            params = json.loads(argv.custom_action_param)
            
            # 合并配置
            config = task_config.copy()
            if "fleets" in params:
                config["option"]["fleets"] = params["fleets"]
            
            max_iterations = params.get("max_iterations", None)
            
            # 创建调度器并运行
            scheduler = FleetScheduler(config, context)
            scheduler.run(max_iterations=max_iterations)
            
            logger.info("自动远征系统结束")
            
            return CustomAction.RunResult(success=True)
            
        except Exception as e:
            logger.error(f"自动远征系统运行出错: {e}", exc_info=True)
            return CustomAction.RunResult(success=False)

# ===============================
# 对比测试：旧版 vs 新版
# ===============================
def compare_methods():
    """对比两种方法的检测次数"""
    print("\n" + "=" * 70)
    print("📊 方法对比：统一间隔 vs 独立计时器")
    print("=" * 70)
    
    # 假设场景
    fleets = [
        {"id": 2, "duration": 12},
        {"id": 5, "duration": 20},
        {"id": 6, "duration": 15}
    ]
    
    print("\n【方法1】统一检测间隔（10秒）:")
    print("-" * 70)
    total_time = 60  # 60秒内
    check_interval = 10
    checks_old = 0
    
    for t in range(0, total_time + 1, check_interval):
        if t == 0:
            continue
        checks_old += len(fleets)
        print(f"  {t}s: 检测所有舰队 ({len(fleets)}次检测)")
    
    print(f"\n总检测次数: {checks_old}")
    
    print("\n【方法2】独立计时器（精确模式）:")
    print("-" * 70)
    checks_new = 0
    
    for fleet in fleets:
        checks_in_60s = 60 // fleet["duration"]
        checks_new += checks_in_60s
        print(f"  舰队{fleet['id']} (周期{fleet['duration']}s): 约 {checks_in_60s} 次检测")
    
    print(f"\n总检测次数: {checks_new}")
    
    reduction = (checks_old - checks_new) / checks_old * 100
    print(f"\n✨ 检测次数减少: {checks_old - checks_new} 次 ({reduction:.1f}%)")
    print("=" * 70)

# ===============================
# 主入口（测试模式）
# ===============================
if __name__ == "__main__":
    # 测试配置（使用更短的时间）
    test_config = task_config.copy()
    test_config["option"]["fleets"] = [
        {"id": 2, "duration": 12, "check_strategy": "exact"},
        {"id": 5, "duration": 20, "check_strategy": "early"},
        {"id": 6, "duration": 15, "check_strategy": "adaptive"}
    ]
    
    # 先显示对比
    compare_methods()
    
    print("\n\n按 Enter 开始运行优化版程序（测试模式）...")
    input()
    
    # 运行优化版（测试模式，无Context）
    scheduler = FleetScheduler(test_config, context=None)
    scheduler.run(max_iterations=10)  # 限制迭代次数用于演示
