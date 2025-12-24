import typer
from typing_extensions import Annotated
from rich.console import Console
from cicd.client.commands import cmd_init, cmd_preparedev, cmd_deploy

console = Console() # 美化命令行输出

# 初始化主应用
app = typer.Typer(
    help="🚀 CICD Client Tool - 自动化部署助手",
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich" 
)





@app.command()
def init():
    """🛠️  初始化项目"""
    cmd_init.run()




@app.command()
def preparedev(
    base: Annotated[str, typer.Option("--base", "-b", help="指定新分支的基准分支 (默认为 main)")] = "main"
):
    """
    🌿 开始新任务：创建并切换到 Feature/Fix 分支

    \b
    日常开发的高频入口。它将：
    1. 🔄 [bold]同步基准[/]：尝试拉取最新的 base 分支代码。
    2. 📝 [bold]交互创建[/]：询问分支类型 (Feat/Fix) 和名称。
    3. 🌿 [bold]自动切换[/]：创建并 Checkout 到新分支。
    """
    cmd_preparedev.run(base_branch=base)



@app.command()
def deploy(
    env: Annotated[str, typer.Option("--env", "-e", help="部署的目标环境 (prod/dev/test)")] = "dev"
):
    """
    🚀 部署发布：安全检查、代码同步与远程构建

    \b
    核心交付入口。将本地代码安全地发布到指定环境。它将：
    1. 🛡️ [bold]git检查[/]：检查当前分支环境是否有未提交的更改。
    2. 📤 [bold]同步推送[/]：推送代码并获取唯一的 Commit Hash。
    3. 📡 [bold]远程触发[/]：唤醒目标服务器 Worker 执行构建与部署。
    """
    cmd_deploy.run(env=env)