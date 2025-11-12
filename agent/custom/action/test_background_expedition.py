"""
测试：后台远征 + 其他任务同时运行
演示如何让远征系统在后台运行，不阻塞其他任务
"""

import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

def simulate_background_expedition():
    """模拟后台远征运行"""
    print("="*70)
    print("演示：后台远征 + 其他任务同时执行")
    print("="*70)
    print()
    
    print("场景说明:")
    print("  1. 启动后台远征系统")
    print("  2. 远征在后台持续运行")
    print("  3. 同时执行其他任务（日常、关卡等）")
    print("  4. 所有任务完成后停止远征")
    print()
    
    # 模拟启动后台远征
    print("[00:00] 🚀 启动后台远征系统...")
    print("[00:00]   → 第2队开始远征（12分钟）")
    print("[00:00]   → 第5队开始远征（20分钟）")
    print("[00:00]   → 第6队开始远征（15分钟）")
    print("[00:00] ✅ 后台远征已启动，其他任务可以继续执行")
    print()
    
    # 模拟执行其他任务
    other_tasks = [
        ("日常任务1", 3),
        ("日常任务2", 2),
        ("关卡5-2", 5),
        ("补给", 1),
        ("演习", 4)
    ]
    
    print("开始执行其他任务:")
    print("-"*70)
    
    current_time = 0
    for task_name, duration in other_tasks:
        print(f"[{current_time:02d}:{(current_time%60):02d}] 📋 执行: {task_name}")
        
        # 模拟任务执行
        for i in range(duration):
            current_time += 1
            # 随机显示后台远征日志
            if current_time % 3 == 0:
                fleet_id = (current_time // 3) % 3 + 2
                print(f"[{current_time:02d}:{(current_time%60):02d}]   [后台] 第{fleet_id}队检测中...")
            time.sleep(0.3)  # 加速演示
        
        print(f"[{current_time:02d}:{(current_time%60):02d}] ✅ 完成: {task_name}")
        print()
    
    print("-"*70)
    print(f"[{current_time:02d}:{(current_time%60):02d}] 所有任务完成")
    print(f"[{current_time:02d}:{(current_time%60):02d}] 🛑 停止后台远征...")
    print(f"[{current_time:02d}:{(current_time%60):02d}] ✅ 远征系统已停止")
    print()
    
    print("="*70)
    print("总结:")
    print("  ✅ 后台远征持续运行，未阻塞其他任务")
    print(f"  ✅ 在{current_time}秒内完成了{len(other_tasks)}个任务")
    print("  ✅ 远征在后台自动收取和派出")
    print("="*70)

def show_code_example():
    """显示代码示例"""
    print("\n\n")
    print("="*70)
    print("代码示例：如何在 Pipeline 中使用")
    print("="*70)
    print()
    
    print("【方式1】直接在 JSON Pipeline 中配置")
    print("-"*70)
    print('''
{
  "MainTask": {
    "next": ["StartExpedition", "DailyTask1"]
  },
  
  "StartExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\\"mode\\": \\"start\\", \\"background\\": true}"
  },
  
  "DailyTask1": {
    "action": "Click",
    "target": "日常任务入口",
    "next": ["DailyTask2"]
  },
  
  "DailyTask2": {
    "recognition": "TemplateMatch",
    "template": "任务2.png",
    "next": ["StopExpedition"]
  },
  
  "StopExpedition": {
    "action": "Custom",
    "custom_action": "AutoExpedition",
    "custom_action_param": "{\\"mode\\": \\"stop\\"}"
  }
}
    ''')
    
    print("\n【方式2】在 Python 代码中使用")
    print("-"*70)
    print('''
# 启动后台远征
context.run_task("StartExpedition")

# 继续执行其他任务
context.run_task("DailyTask1")
context.run_task("DailyTask2")
context.run_task("Combat5-2")

# 停止远征
context.run_task("StopExpedition")
    ''')
    
    print()
    print("="*70)

def compare_modes():
    """对比前台和后台模式"""
    print("\n\n")
    print("="*70)
    print("前台模式 vs 后台模式 对比")
    print("="*70)
    print()
    
    print("【前台模式】(background: false)")
    print("-"*70)
    print("流程:")
    print("  1. 启动远征")
    print("  2. ⏸️  等待远征完成...")
    print("  3. ⏸️  检测...")
    print("  4. ⏸️  收取...")
    print("  5. ⏸️  重新派出...")
    print("  6. ✅ 远征结束，继续执行其他任务")
    print()
    print("特点:")
    print("  ✅ 简单，易于控制")
    print("  ❌ 阻塞执行，其他任务必须等待")
    print("  ❌ 效率低")
    print()
    
    print("【后台模式】(background: true)")
    print("-"*70)
    print("流程:")
    print("  1. 启动后台远征")
    print("  2. ✅ 立即返回，继续执行")
    print("  3. 🔄 远征在后台自动运行")
    print("  4. 📋 同时执行其他任务")
    print("  5. 🛑 任务完成后停止远征")
    print()
    print("特点:")
    print("  ✅ 不阻塞，效率高")
    print("  ✅ 可以同时进行多个任务")
    print("  ✅ 远征自动管理")
    print("  ⚠️  需要手动停止（或程序退出自动停止）")
    print()
    
    print("="*70)
    print("推荐:")
    print("  - 只运行远征 → 使用前台模式")
    print("  - 远征 + 其他任务 → 使用后台模式 ⭐")
    print("="*70)

def main():
    """主函数"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "自动远征 - 后台模式演示" + " "*22 + "║")
    print("╚" + "="*68 + "╝")
    
    # 演示1：后台运行
    simulate_background_expedition()
    
    # 演示2：代码示例
    show_code_example()
    
    # 演示3：模式对比
    compare_modes()
    
    print("\n\n")
    print("="*70)
    print("✨ 现在你可以：")
    print("="*70)
    print("1. 修改 远征确认.json，添加 background: true 参数")
    print("2. 启动后台远征，然后执行其他任务")
    print("3. 查看日志中的 [ExpeditionThread] 标记")
    print("4. 所有任务完成后停止远征")
    print("="*70)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n演示已取消")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
