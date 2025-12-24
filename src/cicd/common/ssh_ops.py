"""SSH 操作工具类"""
import subprocess
from typing import Optional


class SSHOps:
    """SSH 远程命令执行工具类
    
    使用系统 ssh 命令执行远程操作，前提 SSH Key 已配置。
    """
    
    def __init__(self, host: Optional[str] = None, user: Optional[str] = None, 
                 port: int = 22):
        """初始化 SSH 操作工具
        
        Args:
            host: 远程主机地址
            user: 远程用户名
            port: SSH 端口，默认为 22
        """
        self.host = host
        self.user = user
        self.port = port
    
    def run_remote_command(self, command: str) -> str:
        """在远程服务器上执行命令
        
        Args:
            command: 要执行的远程命令
            
        Returns:
            命令的标准输出
            
        Raises:
            ValueError: 当缺少必要参数时
            RuntimeError: 当远程命令执行失败时
        """
        # 使用传入参数或默认值
        target_host = self.host
        target_user = self.user
        target_port = self.port
        
        if not target_host:
            raise ValueError("必须提供远程主机地址 (host)")
        if not target_user:
            raise ValueError("必须提供远程用户名 (user)")
        
        # 构建 SSH 命令
        ssh_target = f"{target_user}@{target_host}"
        ssh_cmd = ["ssh", "-p", str(target_port), ssh_target, command]
        
        try:
            result = subprocess.run(
                ssh_cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else "未知错误"
            raise RuntimeError(
                f"远程命令执行失败 (exit code: {e.returncode}): {error_msg}"
            )
        except FileNotFoundError:
            raise RuntimeError("ssh 命令不可用，请确保系统已安装 OpenSSH")
    
    def test_connection(self, host: Optional[str] = None, 
                       user: Optional[str] = None,
                       port: Optional[int] = None) -> bool:
        """测试 SSH 连接是否正常
        
        Args:
            host: 远程主机地址
            user: 远程用户名
            port: SSH 端口
            
        Returns:
            连接成功返回 True，否则返回 False
        """
        try:
            self.run_remote_command("echo 'connection test'", host, user, port)
            return True
        except (ValueError, RuntimeError):
            return False
