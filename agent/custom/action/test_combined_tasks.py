"""
测试演示：远征 + 5-2出击 组合任务
模拟两个任务的协调运行
"""

import time
import threading

print("="*70)
print("组合任务演示：远征 + 5-2出击")
print("="*70)

# 全局控制
stop_event = threading.Event()
combat_pause_event = threading.Event()
combat_pause_event.set()  # 初始允许出击

from .include import *

@AgentServer.custom_action("combinedtest")
class combinedtest(CustomAction):
    logger.info(" combinedtest 类定义完成，装饰器已执行")

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        logger.info(f"combinedtest 开始运行")

        main()

        logger.info("任务停止")
        return CustomAction.RunResult(success=True)



def simulate_expedition():
    """模拟远征线程"""
    print("\n[远征] 线程启动")
    
    # 模拟3个舰队，简化时间
    fleets = [
        {"id": 2, "duration": 10},
        {"id": 5, "duration": 15},
        {"id": 6, "duration": 12}
    ]
    
    fleet_states = {}
    
    # 初始化
    for fleet in fleets:
        fid = fleet["id"]
        print(f"[远征]  初始化第{fid}队...")
        
        # 初次派出需要暂停5-2
        print(f"[远征]   暂停5-2（初始派出第{fid}队）")
        combat_pause_event.clear()
        time.sleep(0.5)
        
        print(f"[远征]  第{fid}队开始远征（{fleet['duration']}秒）")
        fleet_states[fid] = {
            "finish_time": time.time() + fleet['duration'],
            "duration": fleet['duration']
        }
        time.sleep(0.5)
        
        print(f"[远征]   恢复5-2（第{fid}队已派出）")
        combat_pause_event.set()
        time.sleep(0.3)
    
    print("[远征]  所有舰队初始化完成\n")
    
    # 主循环
    cycle = 0
    while not stop_event.is_set() and cycle < 2:  # 限制循环次数用于演示
        time.sleep(1)
        now = time.time()
        
        for fid, state in fleet_states.items():
            if stop_event.is_set():
                break
            
            # 检查是否完成
            if now >= state["finish_time"]:
                cycle += 1
                print(f"\n[远征]  检测第{fid}队...")
                time.sleep(0.3)
                print(f"[远征]  第{fid}队完成！")
                
                # 暂停5-2
                print(f"[远征]   暂停5-2（开始收取和派出第{fid}队）")
                combat_pause_event.clear()
                time.sleep(0.5)
                
                # 收取
                print(f"[远征]  收取第{fid}队奖励")
                time.sleep(1)
                
                # 重新派出
                print(f"[远征]  第{fid}队重新派出")
                state["finish_time"] = time.time() + state["duration"]
                time.sleep(1)
                
                # 恢复5-2
                print(f"[远征]   恢复5-2（第{fid}队已派出）\n")
                combat_pause_event.set()
    
    print("[远征] 线程结束")

def simulate_combat():
    """模拟5-2出击线程"""
    print("[5-2] 线程启动\n")
    
    combat_count = 0
    
    while not stop_event.is_set():
        # 等待允许出击
        combat_pause_event.wait()
        
        if stop_event.is_set():
            break
        
        # 执行出击
        combat_count += 1
        print(f"[5-2]  开始出击 (第{combat_count}次)")
        
        # 模拟出击过程
        for i in range(3):
            if stop_event.is_set() or not combat_pause_event.is_set():
                print(f"[5-2]   出击被暂停")
                break
            time.sleep(1)
        
        if combat_pause_event.is_set() and not stop_event.is_set():
            print(f"[5-2]   出击完成\n")
        
        # 等待一段时间
        for _ in range(2):
            if stop_event.is_set() or not combat_pause_event.is_set():
                break
            time.sleep(1)
    
    print("[5-2] 线程结束")

def main():
    """主函数"""
    print("\n说明:")
    print("  - 远征和5-2同时运行")
    print("  - 远征完成时会暂停5-2")
    print("  - 收取和派出完成后恢复5-2")
    print("  - 按 Ctrl+C 可以提前停止\n")
    
    input("按 Enter 开始演示...")
    print()
    
    # 启动线程
    exp_thread = threading.Thread(target=simulate_expedition, daemon=True, name="Expedition")
    combat_thread = threading.Thread(target=simulate_combat, daemon=True, name="Combat")
    
    exp_thread.start()
    time.sleep(0.5)  # 稍微延迟，让远征先初始化
    combat_thread.start()
    
    # 等待演示完成
    try:
        exp_thread.join()
        stop_event.set()
        combat_thread.join(timeout=2)
    except KeyboardInterrupt:
        print("\n\n用户中断")
        stop_event.set()
        exp_thread.join(timeout=2)
        combat_thread.join(timeout=2)
    
    print("\n" + "="*70)
    print("演示完成！")
    print("="*70)
    print("\n工作原理:")
    print("  1. 远征线程和5-2线程并发运行")
    print("  2. 使用 combat_pause_event 控制5-2的暂停和恢复")
    print("  3. 远征收取时 clear() 事件，5-2会自动暂停")
    print("  4. 派出完成后 set() 事件，5-2自动恢复")
    print("  5. 两个线程通过事件机制精确协调")
    print()
    print("在实际使用中:")
    print("  - 配置 Pipeline 任务")
    print("  - 使用 AutoCombinedTasks 自定义动作")
    print("  - 查看 combined_tasks_config.json 了解详细配置")
    print("="*70)

if __name__ == "__main__":
    main()
