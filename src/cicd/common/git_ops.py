"""Git 操作工具类"""
import subprocess
from pathlib import Path
from typing import Optional


class GitOps:
    """Git 操作工具类
    
    封装常用的 Git 命令操作，不包含任何打印输出。
    """
    
    def __init__(self, work_dir: Optional[str] = None):
        """初始化 Git 操作工具
        
        Args:
            work_dir: 工作目录路径，默认为当前目录
        """
        self.work_dir = Path(work_dir).resolve() if work_dir else Path.cwd()
    
    def run(self, args: list[str]) -> str:
        """执行 git 命令核心封装
        
        Args:
            args: git 命令参数列表
            
        Returns:
            命令输出结果
            
        Raises:
            RuntimeError: 当 git 命令执行失败时
        """
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                check=True
            )
            return res.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git execution failed: {e.stderr.strip()}")
    
    def is_repo(self) -> bool:
        """检查当前目录是否为 Git 仓库
        
        Returns:
            如果是 Git 仓库返回 True，否则返回 False
        """
        try:
            self.run(["rev-parse", "--is-inside-work-tree"])
            return True
        except RuntimeError:
            return False
    
    def create_and_checkout_branch(self, branch_name: str, 
                                   base_branch: Optional[str] = None) -> None:
        """创建分支并切换
        
        如果分支已存在，则直接切换到该分支。
        如果分支不存在，创建新分支并切换。
        
        Args:
            branch_name: 要创建/切换的分支名称
            base_branch: 基于哪个分支创建（可选，默认为当前分支）
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当 Git 操作失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        # 获取本地分支列表
        branches_output = self.run(["branch", "--list"])
        local_branches = [
            line.strip().replace('*', '').strip()
            for line in branches_output.split('\n')
            if line.strip()
        ]
        
        if branch_name in local_branches:
            # 分支已存在，直接切换
            self.run(["checkout", branch_name])
        else:
            # 分支不存在，创建新分支
            if base_branch:
                # 先切换到基础分支
                self.run(["checkout", base_branch])
            
            # 创建并切换到新分支
            self.run(["checkout", "-b", branch_name])
    
    def get_current_branch(self) -> str:
        """获取当前分支名称
        
        Returns:
            当前分支名称
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当获取失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        return self.run(["branch", "--show-current"])
    
    def is_dirty(self) -> bool:
        """检查工作区是否有未提交的更改
        
        Returns:
            如果有未提交的更改返回 True，否则返回 False
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当检查失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        output = self.run(["status", "--porcelain"])
        return bool(output.strip())
    
    def checkout(self, branch: str) -> None:
        """切换到指定分支
        
        Args:
            branch: 分支名称
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当切换失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        self.run(["checkout", branch])
    
    def pull(self, remote: str = "origin", branch: Optional[str] = None) -> None:
        """拉取远程代码
        
        Args:
            remote: 远程仓库名称，默认为 origin
            branch: 分支名称，如果为 None 则拉取当前分支
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当拉取失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        if branch:
            self.run(["pull", remote, branch])
        else:
            self.run(["pull", remote])
    
    def fetch(self, remote: str = "origin", all_remotes: bool = False) -> None:
        """获取远程仓库信息，确保本地能感知到远程的新分支
        
        Args:
            remote: 远程仓库名称，默认为 origin
            all_remotes: 是否获取所有远程仓库，默认为 False
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当获取失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        if all_remotes:
            self.run(["fetch", "--all"])
        else:
            self.run(["fetch", remote])
    
    def push(self, commit_msg: str) -> None:
        """添加、提交并推送代码到远程仓库
        
        Args:
            commit_msg: 提交信息
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当操作失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        # 1. git add .
        self.run(["add", "."])
        
        # 2. git commit -m [commit_msg]
        self.run(["commit", "-m", commit_msg])
        
        # 3. git push
        current_branch = self.get_current_branch()
        try:
            # 尝试普通推送
            self.run(["push"])
        except RuntimeError as e:
            # 如果是因为没有 upstream 导致的失败，则尝试 set-upstream
            if "no upstream branch" in str(e):
                self.run(["push", "--set-upstream", "origin", current_branch])
            else:
                # 其他错误（如冲突）则直接抛出
                raise e
    
    def get_current_commit_hash(self, short: bool = True) -> str:
        """获取当前 HEAD 的 Commit Hash
        
        Args:
            short: 是否返回短哈希（7位），默认为 True
            
        Returns:
            Commit Hash 字符串
            
        Raises:
            ValueError: 当不是 Git 仓库时
            RuntimeError: 当获取失败时
        """
        if not self.is_repo():
            raise ValueError(f"目录不是 Git 仓库: {self.work_dir}")
        
        args = ["rev-parse"]
        if short:
            args.append("--short")
        args.append("HEAD")
        
        return self.run(args)
    

    def init(self) -> None:
        """初始化 Git 仓库"""
        self.run(["init"])

    def add_remote(self, url: str, name: str = "origin") -> None:
        """添加远程仓库"""
        self.run(["remote", "add", name, url])

    def has_remote(self) -> bool:
        """检查是否存在远程仓库配置"""
        if not self.is_repo():
            return False
        
        # 运行 git remote，如果有输出说明有关联
        try:
            output = self.run(["remote"])
            return bool(output.strip())
        except RuntimeError:
            return False
        
    def get_head_hash(self) -> str:
        """检查是否存在 HEAD (是否有提交记录)"""
        try:
            return self.run(["rev-parse", "HEAD"])
        except RuntimeError:
            return ""

    def align_with_remote(self) -> str:
        """[历史对齐] 将本地文件状态与远程仓库历史进行智能对齐
        
        适用场景：
        1. Zip 下载的代码恢复 Git 关联
        2. 本地新项目接入已存在的远程仓库 (解决 fatal: unrelated histories)
        3. 本地新项目接入空远程仓库
        
        Returns:
            str: 操作结果描述
        """
        # 1. 制造一个临时的初始提交
        self.run(["add", "."])
        self.run(["commit", "-m", "chore: temp commit for history alignment"])
        
        # 2. 获取远程历史
        try:
            self.run(["fetch", "origin"])
        except RuntimeError:
            # [修正点 1] 如果网络失败，需要回滚根提交
            # Root Commit 无法使用 reset HEAD~1，必须直接删除 HEAD 引用
            self.run(["update-ref", "-d", "HEAD"])
            raise RuntimeError("无法获取远程仓库信息，请检查网络或权限。")
        
        # 3. 智能探测远程分支
        remote_branches = self.run(["branch", "-r"])
        
        target_branch = ""
        if "origin/main" in remote_branches:
            target_branch = "origin/main"
        elif "origin/master" in remote_branches:
            target_branch = "origin/master"
        
        # 4. 分情况处理
        if target_branch:
            # A情况：远程有代码 (Zip 恢复 或 远程有 README)
            self.run(["reset", "--mixed", target_branch])
            return f"成功对接远程分支 {target_branch}，历史记录已修复。"
        else:
            # B情况：远程是空的 (Empty Repo)
            # [修正点 2] 撤销刚才的临时 Root Commit
            # 使用 update-ref -d HEAD 等同于对根提交做 reset --soft
            self.run(["update-ref", "-d", "HEAD"])
            return "远程仓库为空，已保留本地更改，准备好进行初始提交。"