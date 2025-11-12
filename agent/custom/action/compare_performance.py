"""
单线程 vs 多线程性能对比演示
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor

def simulate_check(fleet_id):
    """模拟检测操作（耗时0.5秒）"""
    time.sleep(0.5)
    return fleet_id

def test_single_thread(fleet_count=5):
    """单线程测试"""
    print(f"\n【单线程测试】检测 {fleet_count} 个舰队")
    start = time.time()
    
    for i in range(fleet_count):
        result = simulate_check(i)
        print(f"  完成舰队 {result}")
    
    elapsed = time.time() - start
    print(f"  总耗时: {elapsed:.2f}秒")
    return elapsed

def test_multi_thread(fleet_count=5, workers=3):
    """多线程测试"""
    print(f"\n【多线程测试】检测 {fleet_count} 个舰队（{workers}线程）")
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(simulate_check, i) for i in range(fleet_count)]
        for future in futures:
            result = future.result()
            print(f"  完成舰队 {result}")
    
    elapsed = time.time() - start
    print(f"  总耗时: {elapsed:.2f}秒")
    return elapsed

if __name__ == "__main__":
    print("="*60)
    print("性能对比演示：单线程 vs 多线程")
    print("="*60)
    print("\n假设：每个舰队检测耗时 0.5秒")
    
    # 测试1: 5个舰队
    print("\n" + "="*60)
    print("测试 1: 5个舰队")
    print("="*60)
    time1 = test_single_thread(5)
    time2 = test_multi_thread(5, 3)
    improvement = (time1 - time2) / time1 * 100
    print(f"\n✨ 性能提升: {time1-time2:.2f}秒 ({improvement:.1f}%)")
    
    # 测试2: 10个舰队
    print("\n" + "="*60)
    print("测试 2: 10个舰队")
    print("="*60)
    time1 = test_single_thread(10)
    time2 = test_multi_thread(10, 5)
    improvement = (time1 - time2) / time1 * 100
    print(f"\n✨ 性能提升: {time1-time2:.2f}秒 ({improvement:.1f}%)")
    
    # 结论
    print("\n" + "="*60)
    print("📊 结论")
    print("="*60)
    print("""
1. 多线程在并发检测时确实更快
2. 但对于远征（10-30分钟），节省的几秒可以忽略
3. 单线程更简单、更稳定、更易维护
4. 只有在以下情况才需要多线程：
   - 舰队数量 > 10
   - 检测耗时 > 1秒
   - 经常出现多个舰队同时完成
    """)
