import os
import json
from datetime import datetime
from utils.logger import custom_logger as logger
from PIL import Image
from maa.agent.agent_server import AgentServer
from maa.custom_action import CustomAction
from maa.context import Context
from pynput.mouse import Controller, Button

mouse = Controller()

@AgentServer.custom_action("Screenshot")
class Screenshot(CustomAction):
    print("✅ Screenshot 自定义动作已加载")

    
    """
    自定义截图动作，保存当前屏幕截图到指定目录。
    参数格式:
    {
        "save_dir": "保存截图的目录路径"
    }
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        # image array(BGR)
        screen_array = context.tasker.controller.post_screencap().wait().get()


        # BGR2RGB
        if len(screen_array.shape) == 3 and screen_array.shape[2] == 3:
            rgb_array = screen_array[:, :, ::-1]
        else:
            rgb_array = screen_array
            logger.warning("当前截图并非三通道")

        img = Image.fromarray(rgb_array)

        save_dir = json.loads(argv.custom_action_param)["save_dir"]
        os.makedirs(save_dir, exist_ok=True)
        img.save(f"{save_dir}/{self._get_format_timestamp()}.png")
        logger.info(f"截图保存至 {save_dir}/{self._get_format_timestamp()}.png")

        return CustomAction.RunResult(success=True)

    def _get_format_timestamp(self):

        now = datetime.now()

        date = now.strftime("%Y.%m.%d")
        time = now.strftime("%H.%M.%S")
        milliseconds = f"{now.microsecond // 1000:03d}"

        return f"{date}-{time}.{milliseconds}"
    
@AgentServer.custom_action("gamestart")
class gamestart(CustomAction):
    print("✅ gamestart 自定义动作已加载")

    """
    自定义动作：启动游戏
    匹配gamestart
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        logger.info(f"gamestart")

        return CustomAction.RunResult(success=True)



@AgentServer.custom_action("OverrideRefresh")
class OverrideRefresh(CustomAction):
    print("✅ OverrideRefresh 自定义动作已加载")

    """
    自定义动作：重新载入游戏页面
    右键点击poi刷新按钮，载入后匹配gamestart
    """

    def run(
        self,
        context: Context,
        argv: CustomAction.RunArg,
    ) -> CustomAction.RunResult:

        # 刷新按钮坐标
        mouse.position = (251, 855)
        mouse.click(Button.right, 1)

        logger.info(f"重新载入游戏页面")

        # gamestart匹配
        context.run_task("gamestart")
        logger.info(f"游戏页面载入完成，目前应处于主页面")

        return CustomAction.RunResult(success=True)