"""
完整测试示例 - 演示如何使用优化版远征系统
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from agent.custom.action.expedition_optimized import (
    FleetScheduler,
    task_config,
    compare_methods
)

def test_basic_usage():
    """测试1：基本使用"""
    print("\n" + "="*70)
    print("测试1：基本使用（测试模式）")
    print("="*70)
    
    # 使用短时长进行测试
    test_config = {
        "name": "测试任务",
        "entry": "TestTask",
        "option": {
            "fleets": [
                {"id": 2, "duration": 15, "check_strategy": "exact"},
                {"id": 5, "duration": 25, "check_strategy": "early"},
                {"id": 6, "duration": 20, "check_strategy": "adaptive"}
            ],
            "global_check_interval": 30,
            "strategies": task_config["option"]["strategies"],
            "fleet_regions": {
                2: {"x": 100, "y": 200, "width": 300, "height": 150, "name": "第2队区域"},
                5: {"x": 100, "y": 400, "width": 300, "height": 150, "name": "第5队区域"},
                6: {"x": 100, "y": 600, "width": 300, "height": 150, "name": "第6队区域"}
            },
            "recognition": {
                "complete_task": "CheckExpeditionComplete",
                "threshold": 0.8
            }
        }
    }
    
    # 创建调度器（测试模式，不需要Context）
    scheduler = FleetScheduler(test_config, context=None)
    
    # 运行5次迭代
    scheduler.run(max_iterations=5)
    
    print("\n✅ 测试1完成\n")

def test_different_strategies():
    """测试2：不同策略对比"""
    print("\n" + "="*70)
    print("测试2：不同检测策略对比")
    print("="*70)
    
    strategies = ["exact", "early", "adaptive"]
    
    for strategy in strategies:
        print(f"\n--- 测试 {strategy} 策略 ---")
        
        test_config = {
            "name": f"测试{strategy}",
            "entry": "TestTask",
            "option": {
                "fleets": [
                    {"id": 2, "duration": 20, "check_strategy": strategy}
                ],
                "global_check_interval": 30,
                "strategies": task_config["option"]["strategies"],
                "fleet_regions": {
                    2: {"x": 100, "y": 200, "width": 300, "height": 150, "name": "第2队区域"}
                },
                "recognition": {
                    "complete_task": "CheckExpeditionComplete",
                    "threshold": 0.8
                }
            }
        }
        
        scheduler = FleetScheduler(test_config, context=None)
        scheduler.run(max_iterations=2)
    
    print("\n✅ 测试2完成\n")

def test_multiple_fleets():
    """测试3：多舰队并发"""
    print("\n" + "="*70)
    print("测试3：多舰队并发管理")
    print("="*70)
    
    test_config = {
        "name": "多舰队测试",
        "entry": "TestTask",
        "option": {
            "fleets": [
                {"id": 1, "duration": 10, "check_strategy": "exact"},
                {"id": 2, "duration": 15, "check_strategy": "exact"},
                {"id": 3, "duration": 12, "check_strategy": "exact"},
                {"id": 4, "duration": 18, "check_strategy": "exact"},
            ],
            "global_check_interval": 30,
            "strategies": task_config["option"]["strategies"],
            "fleet_regions": {
                1: {"x": 100, "y": 100, "width": 300, "height": 150, "name": "第1队区域"},
                2: {"x": 100, "y": 300, "width": 300, "height": 150, "name": "第2队区域"},
                3: {"x": 100, "y": 500, "width": 300, "height": 150, "name": "第3队区域"},
                4: {"x": 100, "y": 700, "width": 300, "height": 150, "name": "第4队区域"},
            },
            "recognition": {
                "complete_task": "CheckExpeditionComplete",
                "threshold": 0.8
            }
        }
    }
    
    scheduler = FleetScheduler(test_config, context=None)
    scheduler.run(max_iterations=8)
    
    print("\n✅ 测试3完成\n")

def test_performance_comparison():
    """测试4：性能对比"""
    print("\n" + "="*70)
    print("测试4：性能对比分析")
    print("="*70)
    
    compare_methods()
    
    print("\n✅ 测试4完成\n")

def main():
    """运行所有测试"""
    print("="*70)
    print("优化版自动远征系统 - 完整测试")
    print("="*70)
    
    tests = [
        ("基本使用", test_basic_usage),
        ("策略对比", test_different_strategies),
        ("多舰队管理", test_multiple_fleets),
        ("性能对比", test_performance_comparison),
    ]
    
    print("\n可用测试:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    print(f"  0. 运行所有测试")
    
    choice = input("\n请选择测试 (0-4): ").strip()
    
    if choice == "0":
        # 运行所有测试
        for name, test_func in tests:
            try:
                test_func()
            except Exception as e:
                print(f"\n❌ 测试 '{name}' 失败: {e}")
                import traceback
                traceback.print_exc()
    elif choice in ["1", "2", "3", "4"]:
        idx = int(choice) - 1
        name, test_func = tests[idx]
        try:
            test_func()
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("无效选择")
        return
    
    print("\n" + "="*70)
    print("所有测试完成")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
