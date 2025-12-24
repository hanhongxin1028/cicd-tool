"""deploy 命令实现：代码推送与远程部署触发"""
import os
from rich.console import Console
from rich.prompt import Confirm

from cicd.common.git_ops import GitOps
from cicd.common.ssh_ops import SSHOps
from cicd.common.config_ops import ConfigOps





def run(env: str = "dev") -> None:
    """执行 deploy 命令的核心逻辑
    
    Args:
        env: 目标部署环境 (dev/test/prod)
    """

    console = Console()
    git_ops = GitOps()
    config_ops = ConfigOps()
    

    try:
        # ========== 1. 检查是否有未提交的更改 ==========
        console.print("[bold cyan]🛡️  正在检查是否有未提交的更改...[/]")
        
        if git_ops.is_dirty():
            current_branch = git_ops.get_current_branch()
            push = Confirm.ask(f"当前分支 [{current_branch}] 有未提交的更改，现在是否提交？", default=True)
            if push:
                try:
                    commit_msg = console.input("请简要描述更改内容: ")
                    with console.status("[bold green]📤 正在推送本地代码...[/]"):
                        git_ops.push(commit_msg)

                    console.print("[green]✓[/] 代码推送成功\n")
                
                except RuntimeError as e:
                    console.print("[bold red]❌ 代码推送失败:[/]")
                    console.print(f"   {e}", highlight=False, markup=False)
                    return
            else:
                console.print("[bold red]❌  工作区有未提交的更改，无法部署！[/]")
                console.print("[dim]提示: 请先提交或暂存所有更改[/]")
                console.print("[dim]  - git add .[/]")
                console.print("[dim]  - git commit -m 'your message'[/]")
                console.print("[dim]  - git push[/]")
                return
        

        # ========== 2. 加载配置 ==========
        console.print("[bold cyan]📋 正在加载配置...[/]")
        
        # 2.1. 检查配置文件是否存在
        if not config_ops.has_config():
            console.print("[bold red]❌ 未找到配置文件[/]")
            console.print("[dim]请先运行 'cicd init' 初始化项目[/]")
            return
        
        # 2.2. 检查配置文件是否完整
        if not config_ops.validate_config():
            console.print("[bold red]❌ 配置文件不完整[/]")
            console.print("[dim]请填写必要信息[/]")
            return
        
        # 2.3. 获取部署环境配置
        server_host = config_ops.get_config_value(f"server.host")
        server_user = config_ops.get_config_value(f"server.user")
        server_port = config_ops.get_config_value(f"server.port")
        server_repo_path = config_ops.get_config_value(f"server.repo_path")
        server_cicd_runner_exec = config_ops.get_config_value(f"server.runner_exec")

        
        console.print(f"[green]✓[/] 配置加载成功 (环境: {env})")
        console.print(f"[dim]目标服务器: {server_user}@{server_host}[/]\n")
        
        
        
        
        # ========== 3. 远程服务端部署 ==========
        # 3.1. 创建 SSHOps 实例
        ssh_ops = SSHOps(host=server_host, user=server_user, port=server_port)

        # 3.2. 构建远程命令
        current_branch = git_ops.get_current_branch()
        remote_command = f"{server_cicd_runner_exec} deploy --path {server_repo_path} --env {env} --branch {current_branch} "
        console.print(f"[dim]执行命令: {remote_command}[/]\n")
        
        # 3.3. 执行远程命令
        try:
            result = ssh_ops.run_remote_command(command=remote_command)
            
            # 显示远程执行结果
            if result:
                console.print("[bold green]📥 服务器响应:[/]")
                console.print(result)
            
            console.print("\n[bold green]✅ 部署指令已发送！[/]")
            
        except RuntimeError as e:
            console.print("[bold red]❌ 远程命令执行失败:[/]")
            console.print(f"   {e}", highlight=False, markup=False)
            return
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  操作已取消[/]")
        return
    except Exception as e:
        console.print("[bold red]❌ 发生错误:[/]")
        console.print(f"   {e}", highlight=False, markup=False)
        return
