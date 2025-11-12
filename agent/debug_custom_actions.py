"""
Custom Action 注册诊断工具
用于检查 custom action 是否正确注册到 AgentServer
"""

import sys
from pathlib import Path

# 添加路径
current_dir = Path(__file__).resolve().parent
if current_dir not in sys.path:
    sys.path.insert(0, str(current_dir))

def check_custom_actions():
    print("="*70)
    print("Custom Action 注册诊断工具")
    print("="*70)
    
    try:
        # 1. 导入 AgentServer
        print("\n[1/4] 导入 AgentServer...")
        from maa.agent.agent_server import AgentServer
        print(" AgentServer 导入成功")
        
        # 2. 检查 AgentServer 是否有注册方法
        print("\n[2/4] 检查 AgentServer 属性...")
        if hasattr(AgentServer, '_custom_actions'):
            print(f" AgentServer._custom_actions 存在")
        else:
            print(f"⚠️ AgentServer._custom_actions 不存在，可能使用其他注册方式")
        
        # 3. 导入 custom 模块
        print("\n[3/4] 导入 custom 模块...")
        import custom
        print(" custom 模块导入成功")
        
        # 4. 检查注册的 actions
        print("\n[4/4] 检查已注册的 Custom Actions...")
        
        # 尝试多种方式查找注册的 actions
        found_actions = []
        
        # 方式1: 检查 _custom_actions 属性
        if hasattr(AgentServer, '_custom_actions'):
            actions = getattr(AgentServer, '_custom_actions', {})
            if actions:
                print(f"\n通过 _custom_actions 找到 {len(actions)} 个注册的 action:")
                for name, cls in actions.items():
                    print(f"   {name} -> {cls}")
                    found_actions.append(name)
        
        # 方式2: 检查类属性
        if hasattr(AgentServer, 'custom_action'):
            print(f"\n AgentServer.custom_action 装饰器存在")
        
        # 方式3: 检查模块中的类
        print("\n检查 custom.action 模块中的类:")
        from custom import action as action_module
        action_classes = [
            name for name in dir(action_module) 
            if not name.startswith('_') and name[0].isupper()
        ]
        print(f"找到 {len(action_classes)} 个类:")
        for cls_name in action_classes:
            print(f"  • {cls_name}")
        
        # 总结
        print("\n" + "="*70)
        print("诊断总结:")
        print("="*70)
        
        if found_actions:
            print(f" 成功注册了 {len(found_actions)} 个 Custom Actions:")
            for name in found_actions:
                print(f"   • {name}")
        else:
            print("⚠️ 未找到已注册的 Custom Actions")
            print("\n可能的原因:")
            print("  1. AgentServer 使用的注册方式与预期不同")
            print("  2. 装饰器在 AgentServer 导入前执行")
            print("  3. 模块导入顺序问题")
            print("\n建议:")
            print("  • 检查 maa.agent.agent_server 的源码")
            print("  • 确认装饰器的正确使用方式")
            print("  • 查看 MAA 框架的文档")
        
        # 额外信息
        print("\n" + "="*70)
        print("额外信息:")
        print("="*70)
        print(f"Python 版本: {sys.version}")
        print(f"工作目录: {Path.cwd()}")
        print(f"sys.path:")
        for p in sys.path[:5]:
            print(f"  • {p}")
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n可能的原因:")
        print("  • MAA 框架未正确安装")
        print("  • 依赖项缺失")
        print("\n请运行: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_custom_actions()
