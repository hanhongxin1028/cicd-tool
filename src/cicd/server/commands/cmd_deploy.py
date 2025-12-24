import os
import typer
from rich.console import Console
from rich.panel import Panel

from cicd.common.git_ops import GitOps
from cicd.common.config_ops import ConfigOps
from cicd.server.utils.executor import Executor

console = Console()
executor = Executor()

def run(repo_path: str, env: str, branch: str):
    """
    服务端部署主逻辑
    Args:
        repo_path: 服务器上项目存放路径
        env: 部署环境 (dev, prod, test)
        branch: Git 分支 (main, develop)
    """

    # 1. 检查仓库路径
    abs_repo_path = os.path.abspath(repo_path)
    if not os.path.exists(abs_repo_path):
        console.print(f"[yellow]⚠️  仓库路径不存在，正在自动创建: {abs_repo_path}[/]")
        try:
            # exist_ok=True: 目录已存在也不报错
            # mode=0o755: 设置权限 (rwxr-xr-x)
            os.makedirs(abs_repo_path, mode=0o755, exist_ok=True)
        except OSError as e:
            console.print(f"[red]❌ 无法创建部署目录 (请检查权限): {e}[/]")
            raise typer.Exit(code=1)
    
    os.chdir(abs_repo_path)
    cwd = os.getcwd()
    console.print(Panel(f"🚀 开始部署任务\n路径: {cwd}\n环境: [bold cyan]{env}[/]\n分支: [bold magenta]{branch}[/]", title="CICD Runner"))

    # ----------------------------------------------------
    # 2. 验证 Git 环境
    # ----------------------------------------------------
    git_ops = GitOps(work_dir=cwd)

    if not git_ops.is_repo():
        console.print("[red]❌ 当前目录不是 Git 仓库，无法继续。[/]")
        raise typer.Exit(code=1)

    # ==========================================
    # 3. 同步代码
    # ==========================================
    console.print("[bold blue]1️⃣  同步代码仓库[/]")
    try:
        console.print(f"[dim]⚡ Fetching origin...[/dim]")
        git_ops.fetch() # 默认 fetch origin
        
        console.print(f"[dim]⚡ Checkout {branch}...[/dim]")
        git_ops.checkout(branch)
        
        console.print(f"[dim]⚡ Pulling latest code...[/dim]")
        # 这里指定分支拉取，对应 git pull origin {branch}
        git_ops.pull(branch=branch)
            
    except RuntimeError as e:
        # GitOps 抛出的是 RuntimeError，这里捕获并打印
        console.print(f"[red]❌ 代码同步失败: {e}[/]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]❌ 未知错误: {e}[/]")
        raise typer.Exit(code=1)

    # ----------------------------------------------------
    # 4. 读取配置
    # ----------------------------------------------------
    try:
        # 实例化 ConfigOps (默认读取当前目录下的 cicd-config.yaml)
        config_ops = ConfigOps() 
        config = config_ops.load_config()
        
    except FileNotFoundError:
        console.print("[red]❌ 未找到 cicd-config.yaml，请确认代码库根目录包含该文件[/]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]❌ 配置文件读取失败: {e}[/]")
        raise typer.Exit(code=1)

    # ----------------------------------------------------
    # 5. 解析环境配置
    # ----------------------------------------------------
    environments = config.get("environments", {})
    
    if env not in environments:
        console.print(f"[red]❌ 配置文件中未定义环境: '{env}'[/]")
        console.print(f"[dim]可用环境: {', '.join(environments.keys())}[/]")
        raise typer.Exit(code=1)

    env_config = environments[env]
    steps = env_config.get("steps", [])
    deploy_path = env_config.get("deploy_path", "")

    if not steps:
        console.print(f"[yellow]⚠️  环境 '{env}' 未定义任何 steps，部署结束。[/]")
        return

    # ----------------------------------------------------
    # 5. 准备上下文 (Context)
    # ----------------------------------------------------
    context = {
        "branch": branch,
        "deploy_path": deploy_path,
        "project_name": config.get("project_name", "unknown"),
        "cwd": cwd,
        "env": env
    }

    # ----------------------------------------------------
    # 6. 执行 Steps
    # ----------------------------------------------------
    console.print(f"\n[bold blue]2️⃣  执行部署步骤 ({len(steps)} steps)[/]")
    console.print(f"[dim]Deploy Path: {deploy_path}[/dim]\n")

    for i, step in enumerate(steps, 1):
        console.print(f"[bold]Step {i}/{len(steps)}[/]")
        executor.dispatch_step(step, context)

    console.print(f"\n[bold green]✅ [{env}] 环境部署成功！[/]")