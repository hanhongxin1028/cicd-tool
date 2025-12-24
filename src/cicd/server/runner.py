import typer
from rich.console import Console
from cicd.server.commands import cmd_deploy


console = Console() # 美化命令行输出

# 初始化主应用
app = typer.Typer(
    help="🚀 CICD 服务端 Runner 工具",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich" 
)


# =========================================================
# 🏗️ cicd-runner deploy [--path] [--env] [--branch]
# =========================================================
@app.command()
def deploy(
    repo_path: str = typer.Option(".", "--path", help="服务器 项目 存放路径 (默认为当前目录)"),
    env: str = typer.Option("dev", "--env", help="部署环境 (例如 dev, prod)"),
    branch: str = typer.Option("main", "--branch", help="目标分支"),
):
    """
    [Internal] 执行部署任务
    
    只需提供环境和分支，Runner 会自动读取当前目录下的 cicd-config.yaml 进行执行。
    前提：执行此命令前，CWD (当前工作目录) 必须是 Git 仓库根目录。
    """
    try:
        cmd_deploy.run(repo_path=repo_path, env=env, branch=branch)
    except Exception as e:
        typer.echo(f"❌ 部署发生未捕获异常: {e}")
        raise typer.Exit(code=1)
    

@app.command()
def version():
    """
    显示当前 Runner 版本
    """
    console.print("CICD Runner [bold green]v0.1.0[/bold green]")