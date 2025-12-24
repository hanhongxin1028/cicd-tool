"""preparedev 命令实现：环境同步与分支创建"""
from rich.console import Console
from InquirerPy import inquirer
from InquirerPy.validator import EmptyInputValidator

from cicd.common.git_ops import GitOps


console = Console()
git_ops = GitOps()


def run(base_branch: str = "main") -> None:
    """执行 preparedev 命令的核心逻辑
    
    Args:
        base_branch: 基准分支名称，默认为 main
    """
    try:
        # 1. 脏检查：确保工作区干净
        console.print("[bold cyan]🔍 检查工作区状态...[/]")
        if git_ops.is_dirty():
            console.print("[bold red]❌ 工作区有未提交的更改，请先提交或暂存代码！[/]")
            console.print("[dim]提示: 使用 'git status' 查看更改，'git stash' 暂存更改[/]")
            return
        
        console.print("[green]✓[/] 工作区干净\n")
        
        # 2. 同步基准分支
        console.print(f"[bold cyan]🔄 正在同步 [yellow]{base_branch}[/] 分支...[/]")
        
        try:
            # 切换到基准分支
            git_ops.checkout(base_branch)
            console.print(f"[green]✓[/] 已切换到 {base_branch}")
            
            # 拉取最新代码
            git_ops.pull("origin", base_branch)
            console.print(f"[green]✓[/] 已拉取最新代码")
            
            # 获取远程分支信息
            git_ops.fetch("origin")
            console.print(f"[green]✓[/] 已同步远程分支信息\n")
            
        except RuntimeError as e:
            console.print(f"[bold red]❌ 同步基准分支失败:[/] {e}", markup=False)
            return
        
        # 3. 交互式问答：选择分支类型
        console.print("[bold cyan]📝 请配置新分支信息:[/]\n")
        
        branch_type = inquirer.select(
            message="选择分支类型:",
            choices=[
                {"name": "🎯 feat - 新功能开发", "value": "feat"},
                {"name": "🐛 fix - Bug 修复", "value": "fix"},
                {"name": "🚨 hotfix - 紧急修复", "value": "hotfix"},
                {"name": "🔧 chore - 杂项任务", "value": "chore"},
            ],
            default="feat",
        ).execute()
        
        # 4. 输入任务名称
        task_name = inquirer.text(
            message="输入任务名称 (例如: login-page):",
            validate=EmptyInputValidator("任务名称不能为空"),
            invalid_message="任务名称不能为空，请重新输入"
        ).execute()
        
        # 5. 拼接分支名称
        new_branch = f"{branch_type}/{task_name}"
        
        # 6. 创建并切换到新分支
        console.print(f"\n[bold cyan]🌿 正在创建分支: [yellow]{new_branch}[/]...[/]")
        
        try:
            git_ops.create_and_checkout_branch(new_branch, base_branch)
            console.print(f"[bold green]✨ 已成功切换到分支: [yellow]{new_branch}[/][/]\n")
            
            console.print("[bold green]🎉 准备工作完成！[/]")
            console.print("👉现在，您可以开始编码了，完成后使用 'cicd deploy' 进行部署")
            
        except RuntimeError as e:
            console.print("[bold red]❌ 创建分支失败:[/]")
            console.print(f"   {e}", highlight=False, markup=False)
            return
            
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  操作已取消[/]")
        return
    except Exception as e:
        console.print("[bold red]❌ 发生错误:[/]")
        console.print(f"   {e}", highlight=False, markup=False)
        return
