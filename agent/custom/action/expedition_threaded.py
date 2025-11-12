"""
多线程版自动远征程序
使用线程池实现并发检测，适用于大规模舰队或检测耗时长的场景
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import PriorityQueue

# ===============================
# 配置
# ===============================
task_config = {
    "name": "舰队自动远征 - 多线程版",
    "entry": "MyTask3",
    "option": {
        "fleets": [
            {"id": 2, "duration": 12, "check_strategy": "exact"},
            {"id": 5, "duration": 20, "check_strategy": "early"},
            {"id": 6, "duration": 15, "check_strategy": "adaptive"},
            {"id": 3, "duration": 18, "check_strategy": "exact"},
            {"id": 4, "duration": 25, "check_strategy": "early"}
        ],
        "max_workers": 3,  # 最大并发线程数
        "strategies": {
            "exact": {"check_before": 0, "retry_interval": 5},
            "early": {"check_before": 2, "retry_interval": 3},
            "adaptive": {"check_before_ratio": 0.1, "retry_interval": 5}
        }
    }
}

# ===============================
# 模拟检测函数（带延迟，模拟图像识别）
# ===============================
def check_expedition_complete(fleet_id: int) -> bool:
    """模拟检测远征是否完成（耗时操作）"""
    time.sleep(0.5)  # 模拟图像识别延迟
    return True

def collect_expedition(fleet_id: int):
    thread_name = threading.current_thread().name
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{thread_name}] 💰 收取第 {fleet_id} 队远征奖励")
    time.sleep(0.3)  # 模拟网络请求

def start_expedition(fleet_id: int, duration: int) -> float:
    thread_name = threading.current_thread().name
    now = time.time()
    finish_time = now + duration
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [{thread_name}] 🚢 第 {fleet_id} 队开始远征（{duration}s）")
    return finish_time

# ===============================
# 多线程版调度器
# ===============================
class ThreadedFleetScheduler:
    """多线程舰队调度器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.fleets = config["option"]["fleets"]
        self.strategies = config["option"]["strategies"]
        self.max_workers = config["option"]["max_workers"]
        
        # 使用线程安全的优先队列
        self.check_queue = PriorityQueue()
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        
        # 舰队状态（需要锁保护）
        self.fleet_states: Dict[int, dict] = {}
        self.state_lock = threading.Lock()
        
        # 统计信息（需要锁保护）
        self.stats = {
            "total_checks": 0,
            "successful_collections": 0,
            "failed_checks": 0,
            "concurrent_checks": 0,  # 并发检测次数
            "max_concurrent": 0      # 最大并发数
        }
        self.stats_lock = threading.Lock()
        
        # 运行标志
        self.running = True
    
    def get_check_time(self, fleet_id: int, finish_time: float, strategy_name: str) -> float:
        """根据策略计算检测时间"""
        strategy = self.strategies.get(strategy_name, self.strategies["exact"])
        duration = finish_time - time.time()
        
        if strategy_name == "exact":
            return finish_time - strategy["check_before"]
        elif strategy_name == "early":
            return finish_time - strategy["check_before"]
        elif strategy_name == "adaptive":
            check_before = duration * strategy["check_before_ratio"]
            return finish_time - check_before
        return finish_time
    
    def initialize_fleets(self):
        """初始化所有舰队"""
        print("\n=== 初始化舰队（多线程版）===\n")
        print(f"线程池大小: {self.max_workers}\n")
        
        for fleet_cfg in self.fleets:
            fleet_id = fleet_cfg["id"]
            duration = fleet_cfg["duration"]
            strategy = fleet_cfg.get("check_strategy", "exact")
            
            # 派出远征
            finish_time = start_expedition(fleet_id, duration)
            
            # 计算首次检测时间
            check_time = self.get_check_time(fleet_id, finish_time, strategy)
            
            # 保存状态
            with self.state_lock:
                self.fleet_states[fleet_id] = {
                    "duration": duration,
                    "strategy": strategy,
                    "finish_time": finish_time,
                    "status": "running",
                    "check_count": 0
                }
            
            # 加入检测队列
            self.check_queue.put((check_time, fleet_id, "scheduled"))
            
            remain = int(check_time - time.time())
            print(f"   📋 第 {fleet_id} 队 [{strategy}模式] 将在 {remain}s 后检测")
        
        print("\n=== 舰队初始化完成 ===\n")
    
    def process_check(self, fleet_id: int, check_type: str):
        """处理检测（在工作线程中执行）"""
        thread_name = threading.current_thread().name
        
        # 更新并发统计
        with self.stats_lock:
            self.stats["concurrent_checks"] += 1
            if self.stats["concurrent_checks"] > self.stats["max_concurrent"]:
                self.stats["max_concurrent"] = self.stats["concurrent_checks"]
        
        try:
            with self.state_lock:
                state = self.fleet_states[fleet_id].copy()
                self.fleet_states[fleet_id]["check_count"] += 1
            
            with self.stats_lock:
                self.stats["total_checks"] += 1
            
            strategy = self.strategies[state["strategy"]]
            now = time.time()
            
            # 显示检测信息
            time_to_finish = int(state["finish_time"] - now)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{thread_name}] 🔍 检测第 {fleet_id} 队 "
                  f"[{check_type}] (距预计完成: {time_to_finish}s)")
            
            # 执行检测（耗时操作）
            if now >= state["finish_time"] and check_expedition_complete(fleet_id):
                # 远征完成
                with self.stats_lock:
                    self.stats["successful_collections"] += 1
                
                collect_expedition(fleet_id)
                
                # 重新派出
                new_finish_time = start_expedition(fleet_id, state["duration"])
                
                with self.state_lock:
                    self.fleet_states[fleet_id]["finish_time"] = new_finish_time
                    self.fleet_states[fleet_id]["check_count"] = 0
                
                # 安排下次检测
                next_check = self.get_check_time(fleet_id, new_finish_time, state["strategy"])
                self.check_queue.put((next_check, fleet_id, "scheduled"))
                
                remain = int(next_check - time.time())
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [{thread_name}] ✅ 第 {fleet_id} 队已重新派出，"
                      f"下次检测: {remain}s 后")
            
            else:
                # 未完成，安排重试
                with self.stats_lock:
                    self.stats["failed_checks"] += 1
                
                retry_interval = strategy.get("retry_interval", 5)
                retry_time = now + retry_interval
                self.check_queue.put((retry_time, fleet_id, "retry"))
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [{thread_name}] ⏳ 第 {fleet_id} 队未完成，"
                      f"{retry_interval}s 后重试")
        
        finally:
            # 减少并发计数
            with self.stats_lock:
                self.stats["concurrent_checks"] -= 1
    
    def run(self, max_iterations: int = None):
        """运行调度器（主线程）"""
        self.initialize_fleets()
        
        iteration = 0
        print("=== 开始自动远征循环（多线程）===\n")
        
        futures = []
        
        try:
            while self.running:
                if max_iterations and iteration >= max_iterations:
                    break
                
                # 获取下一个检测任务
                if self.check_queue.empty():
                    time.sleep(0.1)
                    continue
                
                next_check_time, fleet_id, check_type = self.check_queue.get()
                
                # 等待到检测时间
                now = time.time()
                wait_time = next_check_time - now
                
                if wait_time > 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [MainThread] 💤 等待 {int(wait_time)}s...")
                    time.sleep(wait_time)
                
                # 提交到线程池执行
                future = self.executor.submit(self.process_check, fleet_id, check_type)
                futures.append(future)
                
                print("-" * 70)
                iteration += 1
        
        except KeyboardInterrupt:
            print("\n⚠️ 接收到中断信号，正在停止...")
            self.running = False
        
        finally:
            # 等待所有任务完成
            print("\n等待所有任务完成...")
            self.executor.shutdown(wait=True)
            
            # 显示统计
            self.show_statistics()
    
    def show_statistics(self):
        """显示统计信息"""
        print("\n" + "=" * 70)
        print("📊 统计信息（多线程版）")
        print("=" * 70)
        print(f"总检测次数: {self.stats['total_checks']}")
        print(f"成功收取次数: {self.stats['successful_collections']}")
        print(f"失败检测次数: {self.stats['failed_checks']}")
        print(f"最大并发检测数: {self.stats['max_concurrent']}")
        
        if self.stats['successful_collections'] > 0:
            avg = self.stats['total_checks'] / self.stats['successful_collections']
            print(f"平均每次收取检测次数: {avg:.2f}")
        
        print("\n各舰队检测次数:")
        with self.state_lock:
            for fleet_id, state in self.fleet_states.items():
                print(f"  舰队 {fleet_id}: {state['check_count']} 次")
        print("=" * 70)

# ===============================
# 性能对比测试
# ===============================
def performance_comparison():
    """对比单线程 vs 多线程性能"""
    print("\n" + "=" * 70)
    print("⚡ 性能对比：单线程 vs 多线程")
    print("=" * 70)
    
    print("\n假设场景：")
    print("  - 5个舰队同时到期需要检测")
    print("  - 每次检测耗时 0.5秒（图像识别）")
    print("  - 每次收取耗时 0.3秒（网络请求）")
    
    print("\n【单线程】")
    print("  检测: 0.5s × 5 = 2.5s")
    print("  收取: 0.3s × 5 = 1.5s")
    print("  派出: 忽略不计")
    print("  总耗时: 4.0s")
    
    print("\n【多线程（3个线程）】")
    print("  第1批(3个): 0.5s + 0.3s = 0.8s")
    print("  第2批(2个): 0.5s + 0.3s = 0.8s")
    print("  总耗时: 1.6s")
    
    print("\n✨ 性能提升: 2.4s (60%)")
    
    print("\n但是...")
    print("  远征通常 > 10分钟，节省的 2.4秒可以忽略")
    print("  除非舰队数量很多（> 10个）或检测很频繁")
    print("=" * 70)

# ===============================
# 主入口
# ===============================
if __name__ == "__main__":
    # 先显示性能对比
    performance_comparison()
    
    print("\n\n按 Enter 开始运行多线程版程序...")
    input()
    
    # 运行多线程版
    scheduler = ThreadedFleetScheduler(task_config)
    scheduler.run(max_iterations=10)  # 限制迭代次数用于演示
