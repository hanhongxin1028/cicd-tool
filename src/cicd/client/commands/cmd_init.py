from rich.console import Console
from rich.prompt import Prompt, Confirm

from cicd.common.config_ops import ConfigOps
from cicd.common.git_ops import GitOps


# 工具声明
console = Console()         # 日志工具
git_ops = GitOps()          # Git 操作工具
config_ops = ConfigOps()    # 配置文件操作工具



def run():
    """初始化项目
    
    检查流程：
    1. 检查是否为 Git 仓库
    2. 检查配置文件是否存在（不存在则提示创建）
    3. 两者都满足后提示用户执行 preparedev 命令
    """
    console.print("[bold blue]📦 正在进行就绪检测...[/]")

    # 1. 检查本地 Git 仓库
    if not git_ops.is_repo():
        console.print("[yellow]⚠️  当前目录不是 Git 仓库。[/]")
        
        if Confirm.ask("是否在此目录初始化 Git 仓库?", default=True):
            try:
                git_ops.init()
                console.print("[green]✓[/] Git 仓库初始化成功")
            except Exception as e:
                console.print(f"[red]❌ 初始化失败: {e}[/]")
                return
        else:
            console.print("[red]❌ 必须在 Git 仓库下运行。程序退出。[/]")
            console.print("[dim]提示: 请先使用 'git init' 初始化仓库。[/]")
            return
    else:
        console.print("[green]✓[/] Git 仓库检查通过")


    # 2. 远程仓库关联检查
    if not git_ops.has_remote():
        console.print("[yellow]⚠️  当前仓库未关联远程仓库 (Remote)。[/]")
        
        if Confirm.ask("必须关联远程仓库才能继续，是否现在关联?", default=True):
            try:
                remote_url = Prompt.ask("请输入远程仓库 URL")
                if not remote_url:
                    console.print("[red]❌ URL 不能为空。程序退出。[/]")
                    return
                
                git_ops.add_remote(remote_url)
                console.print("[green]✓[/] 远程仓库关联成功")
            except Exception as e:
                console.print(f"[red]❌ 关联远程仓库失败: {e}[/]")
                return
        else:
            console.print("[red]❌ 未关联远程仓库，无法进行后续部署检查。程序退出。[/]")
            return
    else:
        console.print("[green]✓[/] 远程仓库检查通过")

    # 3. 检查是否有 git 提交历史（适用于首次初始化项目 或 zip下载代码的情况）
    if not git_ops.get_head_hash() and git_ops.is_dirty():
        console.print("\n[yellow]⚠️  检测到本地有代码文件，但尚未建立 Git 提交历史。[/]")
                    
        if Confirm.ask("是否自动同步远程历史 (推荐)?", default=True):
            try:
                with console.status("[bold green]正在对齐远程历史...[/]"):
                    result_msg = git_ops.align_with_remote()
                    console.print(f"[green]✓[/] {result_msg}")
            except Exception as e:
                console.print(f"[red]❌ 同步失败 (请检查远程分支是否存在): {e}[/]")
                return
            
    
    # 2. 检查配置文件
    if not config_ops.has_config():
        console.print(f"[yellow]⚠️  未找到配置文件: {config_ops.config_name}[/]")
        
        # 提示用户是否创建
        create = Confirm.ask("是否创建默认配置文件?", default=True)
        
        if create:
            try:
                config_path = config_ops.create_default_config()
                console.print(f"[green]✓[/] 配置文件已创建: {config_path}")
                console.print("[dim]请根据项目需求编辑配置文件后再继续。[/]")
                return
            except Exception as e:
                console.print(f"[red]❌ 创建配置文件失败: {e}[/]")
                return
        else:
            console.print("[yellow]已取消初始化。[/]")
            return
    else:
        console.print(f"[green]✓[/] 配置文件已存在: {config_ops.config_name}")
        
        # 验证配置文件
        is_valid, errors = config_ops.validate_config()
        if not is_valid:
            console.print("[yellow]⚠️  配置文件存在以下问题:[/]")
            for error in errors:
                console.print(f"  - {error}")
            console.print("[dim]建议修复配置问题后再继续。[/]")
            return

    # 3. 初始化成功提示
    console.print("\n[bold green]✨ 就绪检测完成！[/]")
    console.print("\n[bold yellow]若显示有未提交的更改，请手动提交并推送初始代码：")
    console.print("   [dim]$ git add .[/]")
    console.print("   [dim]$ git commit -m 'Initial commit'[/]")
    console.print("   [dim]$ git push -u origin main[/]")
    
    console.print("\n👉 然后执行 [bold cyan]cicd preparedev[/] 开始开发")