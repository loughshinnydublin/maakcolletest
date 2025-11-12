import os
import sys
import json
import subprocess
from pathlib import Path


# 将当前目录添加到路径
current_dir = Path(__file__).resolve().parent
interface_path = (current_dir / "../assets/interface.json").resolve()
print(f"当前目录: {current_dir}")
project_root_dir = current_dir.parent
print(f"项目根目录: {project_root_dir}")

if current_dir not in sys.path:
    sys.path.insert(0, current_dir)


VENV_NAME = ".venv"  # 虚拟环境目录的名称
VENV_DIR = Path(project_root_dir) / VENV_NAME

try:
    from utils.logger import custom_logger as logger
except ImportError:
    print("无法导入自定义logger模块，使用默认logger")
    # 如果logger不存在，创建一个简单的logger
    import logging

    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
    )
    logger = logging


def read_interface_version() -> str:
    print(f"读取 interface.json 版本: {interface_path}")
    if not interface_path.exists():
        logger.warning("interface.json 文件不存在，无法读取版本")
        return "unknown"

    try:
        with open(interface_path, "r", encoding="utf-8") as f:
            interface_data = json.load(f)
            return interface_data.get("version", "unknown")
    except Exception:
        logger.exception("读取interface.json版本失败")
        return "unknown"


def read_pip_config() -> dict:
    config_dir = Path("./config")
    config_dir.mkdir(exist_ok=True)

    config_path = config_dir / "pip_config.json"
    default_config = {
        "enable_pip_install": True,
        "last_version": "unknown"
    }

    if not config_path.exists():
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("读取pip配置失败，使用默认配置")
        return default_config


def update_pip_config(version) -> bool:
    config_path = Path("./config/pip_config.json")
    try:
        config = read_pip_config()
        config["last_version"] = version

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        return True
    except Exception:
        logger.exception("更新pip配置失败")
        return False


def install_requirements(req_file="requirements.txt", mirror=None) -> bool:
    req_path = Path(req_file)
    if not req_path.exists():
        logger.error(f"requirements.txt 不存在")
        return False

    try:
        logger.info("开始安装依赖...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_path)]

        subprocess.check_call(cmd)
        logger.info("依赖安装完成")
        return True
    except:
        logger.exception("pip 安装依赖时出错")
        return False


def check_and_install_dependencies():
    pip_config = read_pip_config()
    current_version = read_interface_version()
    last_version = pip_config.get("last_version", "unknown")
    enable_pip_install = pip_config.get("enable_pip_install", True)

    logger.info(f"当前版本: {current_version}, 上次运行版本: {last_version}")
    logger.info(f"启用 pip 安装依赖: {enable_pip_install}")

    if enable_pip_install and (
        current_version != last_version or current_version == "unknown"
    ):
        if install_requirements():
            update_pip_config(current_version)
            logger.info("依赖检查完成")
        else:
            logger.warning("依赖安装失败，程序可能无法正常运行")
    else:
        logger.info("跳过依赖安装")


def _is_running_in_our_venv():
    """检查脚本是否在此脚本管理的特定venv中运行。"""
    current_python = Path(sys.executable).resolve()

    logger.debug(f"当前Python解释器: {current_python}")

    if sys.platform.startswith("win"):
        # Windows: 如果在虚拟环境中，Python应该在 Scripts 目录下
        if current_python.parent.name == "Scripts":
            return True
        else:
            logger.debug("当前不在目标虚拟环境中")
            return False
    else:
        # Linux/Unix: 如果在虚拟环境中，Python应该在 bin 目录下
        if current_python.parent.name == "bin":
            return True
        else:
            logger.debug("当前不在目标虚拟环境中")
            return False


def ensure_venv_and_relaunch_if_needed():
    """
    确保venv存在，并且如果尚未在脚本管理的venv中运行，
    则在其中重新启动脚本。支持Linux和Windows系统。
    """
    logger.info(f"检测到系统: {sys.platform}。当前Python解释器: {sys.executable}")

    if _is_running_in_our_venv():
        logger.info(f"已在目标虚拟环境 ({VENV_DIR}) 中运行。")
        return

    if not VENV_DIR.exists():
        logger.info(f"正在 {VENV_DIR} 创建虚拟环境...")
        try:
            # 使用当前运行此脚本的Python（系统/外部Python）
            subprocess.run(
                [sys.executable, "-m", "venv", str(VENV_DIR)],
                check=True,
                capture_output=True,
            )
            logger.info(f"创建成功")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"创建失败: {e.stderr.decode(errors='ignore') if e.stderr else e.stdout.decode(errors='ignore')}"
            )
            logger.error("正在退出")
            sys.exit(1)
        except FileNotFoundError:
            logger.error(
                f"命令 '{sys.executable} -m venv' 未找到。请确保 'venv' 模块可用。"
            )
            logger.error("无法在没有虚拟环境的情况下继续。正在退出。")
            sys.exit(1)

    if sys.platform.startswith("win"):
        python_in_venv = VENV_DIR / "Scripts" / "python.exe"
    else:
        python3_path = VENV_DIR / "bin" / "python3"
        python_path = VENV_DIR / "bin" / "python"
        if python3_path.exists():
            python_in_venv = python3_path
        elif python_path.exists():
            python_in_venv = python_path
        else:
            python_in_venv = python3_path  # 默认使用python3，让后续错误处理捕获

    if not python_in_venv.exists():
        logger.error(f"在虚拟环境 {python_in_venv} 中未找到Python解释器。")
        logger.error("虚拟环境创建可能失败或虚拟环境结构异常。")
        sys.exit(1)

    logger.info(f"正在使用虚拟环境Python重新启动")

    try:
        cmd = [str(python_in_venv)] + sys.argv
        logger.info(f"执行命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=os.getcwd(),
            env=os.environ.copy(),
            check=False,  # 不在非零退出码时抛出异常
        )
        # 退出时使用子进程的退出码
        sys.exit(result.returncode)

    except Exception as e:
        logger.exception(f"在虚拟环境中重新启动脚本失败: {e}")
        sys.exit(1)



def agent(is_dev_mode=False):
    try:
        # 清理模块缓存（但不清理 custom 模块）
        utils_modules = [
            name for name in list(sys.modules.keys()) 
            if name.startswith("utils") and not name.startswith("custom")
        ]
        for module_name in utils_modules:
            del sys.modules[module_name]

        from maa.agent.agent_server import AgentServer
        from maa.toolkit import Toolkit

        # 重要：在 AgentServer 导入后立即导入 custom 以注册装饰器
        import custom
        
        logger.info("Custom actions 模块已加载")

        Toolkit.init_option("./")

        if len(sys.argv) < 2:
            if is_dev_mode:
                # 开发模式下使用默认socket_id进行测试
                socket_id = "test_socket_id"
                logger.warning(f"开发模式: 使用默认socket_id: {socket_id}")
            else:
                logger.error("缺少必要的 socket_id 参数")
                logger.error("用法: python main.py <socket_id>")
                return
        else:
            socket_id = sys.argv[-1]
            logger.info(f"socket_id: {socket_id}")

        AgentServer.start_up(socket_id)
        logger.info("AgentServer启动")
        AgentServer.join()
        AgentServer.shut_down()
        logger.info("AgentServer关闭")
    except ImportError as e:
        logger.error(f"导入模块失败: {e}")
        logger.error("考虑重新配置环境")
        sys.exit(1)
    except Exception as e:
        logger.exception("agent运行过程中发生异常")
        raise



def main():

    current_version = read_interface_version()
    # current_version = "DEBUG"  # 取消注释此行以启用开发模式
    is_dev_mode = current_version == "DEBUG"
    
    logger.info(f"当前版本: {current_version}, 开发模式: {is_dev_mode}")

    # 如果是Linux系统或开发模式，启动虚拟环境
    if sys.platform.startswith("linux") or is_dev_mode:
        ensure_venv_and_relaunch_if_needed()

    check_and_install_dependencies()

    if is_dev_mode:
        os.chdir(Path("../assets"))
        logger.info(f"set cwd: {os.getcwd()}")

    agent(is_dev_mode=is_dev_mode)

    # check_and_install_dependencies()
    # agent()


if __name__ == "__main__":
    main()