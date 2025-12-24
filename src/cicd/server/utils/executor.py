import subprocess
from typing import Dict, Any, Union
# 引入插件
from cicd.server.actions import nginx

class Executor:
    """执行器：负责逻辑分发"""

    @staticmethod
    def run_shell(cmd: str) -> None:
        """
        执行 Shell 命令
        
        Raises:
            subprocess.CalledProcessError: 执行失败时抛出
        """
        # 这里不捕获 stdout，允许命令自身的输出直接显示在终端（如 npm install 的进度条）
        # 但 Executor 本身不产生额外的 print
        subprocess.run(cmd, shell=True, check=True)

    @staticmethod
    def dispatch_step(step: Union[str, Dict], context: Dict[str, Any]) -> None:
        """
        分发步骤
        
        Raises:
            KeyError: 变量替换失败
            ValueError: 格式错误
            RuntimeError: 执行过程错误
        """
        
        # 场景 A: 字符串 -> Shell 执行
        if isinstance(step, str):
            try:
                # 变量替换
                cmd = step.format(**context)
                Executor.run_shell(cmd)
            except KeyError as e:
                raise KeyError(f"配置文件使用了未知变量: {e}")
            except subprocess.CalledProcessError:
                # 抛出异常让上层捕获
                raise RuntimeError(f"Shell 命令执行失败: {cmd}")

        # 场景 B: 字典 -> Action 部署
        elif isinstance(step, dict) and "action" in step:
            action_name = step["action"]
            
            if action_name == "nginx":
                # 直接调用 action 模块
                nginx.run(context)
            else:
                raise ValueError(f"不支持的 Action 类型: {action_name}")
                
        else:
            raise ValueError(f"无法识别的步骤格式: {step}")