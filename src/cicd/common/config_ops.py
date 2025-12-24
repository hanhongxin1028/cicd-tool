"""配置管理工具类"""
import yaml
from pathlib import Path
from typing import Optional, Dict, Any


class ConfigOps:
    """配置文件管理工具类
    
    负责配置文件的创建、检查和读写操作。
    """
    
    DEFAULT_CONFIG_NAME = "cicd-config.yaml"
    
    DEFAULT_CONFIG_TEMPLATE = {
        # 项目名称
        "project_name": "your-project-name",

        # 服务器基础配置 (所有环境共用)
        "server": {
            "host": "your-server-ip",     # 目标服务器 IP
            "user": "your-ssh-username",              # SSH 用户名
            "repo_path": "/data/repos/your-project", # 源码拉取目录
            "port": 22,                # 可选：默认 22
            "key_file": "~/.ssh/id_rsa", # 可选：指定私钥路径
            # 场景 A: 标准 venv (指向具体的可执行文件)
            "runner_exec": "/home/jscn/cicd-test/cicd-tool/.venv/bin/cicd-runner"
            
            # 场景 B: Conda 环境
            # runner_exec: "/home/jscn/miniconda3/envs/cicd/bin/cicd-runner"
            
            # 场景 C: 全局安装 (在 PATH 中)
            # runner_exec: "cicd-runner"
        },

        # 环境定义
        "environments": {
            # 场景 A: 生产环境 (前端项目示例 - 构建并搬运)
            "prod": {
                "deploy_path": "/apps/your-project/", # 最终产物目录 (Nginx Root)
                "steps": [
                    "npm install",
                    "npm run build:prod",
                    "rm -rf {deploy_path}/*",
                    "cp -r dist/* {deploy_path}",
                    {"action": "nginx"}
                ]
            },

            # 场景 B: 测试环境 (原地构建示例)
            "test": {
                "deploy_path": "/data/repos/your-project/dist",
                "steps": [
                    "npm install",
                    "npm run build:test"
                ]
            },

            # 场景 C: 开发环境
            "dev": {
                "deploy_path": "/data/repos/your-project/dist",
                "steps": [
                    "npm install",
                    "npm run build:dev"
                ]
            }
        }
    }
    
    def __init__(self, work_dir: Optional[str] = None, 
                 config_name: Optional[str] = None):
        """初始化配置管理器
        
        Args:
            work_dir: 工作目录路径，默认为当前目录
            config_name: 配置文件名称，默认为 cicd-config.yaml
        """
        self.work_dir = Path(work_dir).resolve() if work_dir else Path.cwd()
        self.config_name = config_name or self.DEFAULT_CONFIG_NAME
        self.config_path = self.work_dir / self.config_name
    
    def has_config(self) -> bool:
        """检查配置文件是否存在
        
        Returns:
            如果配置文件存在返回 True，否则返回 False
        """
        return self.config_path.exists() and self.config_path.is_file()
    
    def create_default_config(self, overwrite: bool = False) -> Path:
        """创建默认配置文件
        
        Args:
            overwrite: 如果文件已存在是否覆盖，默认为 False
            
        Returns:
            配置文件路径
            
        Raises:
            FileExistsError: 当文件已存在且 overwrite=False 时
        """
        if self.has_config() and not overwrite:
            raise FileExistsError(
                f"配置文件已存在: {self.config_path}。"
                "如需覆盖，请设置 overwrite=True"
            )
        
        # 确保目录存在
        self.work_dir.mkdir(parents=True, exist_ok=True)
        
        # 写入默认配置
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                self.DEFAULT_CONFIG_TEMPLATE,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
        
        return self.config_path
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件
        
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 当配置文件不存在时
            yaml.YAMLError: 当配置文件格式错误时
        """
        if not self.has_config():
            raise FileNotFoundError(
                f"配置文件不存在: {self.config_path}。"
                "请先使用 create_default_config() 创建配置文件。"
            )
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def save_config(self, config: Dict[str, Any]) -> None:
        """保存配置到文件
        
        Args:
            config: 配置字典
        """
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                config,
                f,
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False
            )
    
    def update_config(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置文件（部分更新）
        
        Args:
            updates: 需要更新的配置项
            
        Returns:
            更新后的完整配置
            
        Raises:
            FileNotFoundError: 当配置文件不存在时
        """
        config = self.load_config()
        self._deep_update(config, updates)
        self.save_config(config)
        return config
    
    def _deep_update(self, base: Dict[str, Any], updates: Dict[str, Any]) -> None:
        """深度更新字典（递归更新嵌套字典）
        
        Args:
            base: 基础字典
            updates: 更新字典
        """
        for key, value in updates.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径）
        
        Args:
            key_path: 配置键路径，如 "server.host" 或 "git.branch"
            default: 默认值
            
        Returns:
            配置值，如果不存在返回默认值
            
        Example:
            config_manager.get_config_value("server.host")
            config_manager.get_config_value("git.branch", "main")
        """
        try:
            config = self.load_config()
            keys = key_path.split('.')
            value = config
            
            for key in keys:
                value = value[key]
            
            return value
        except (FileNotFoundError, KeyError, TypeError):
            return default
    
    def validate_config(self) -> tuple[bool, list[str]]:
        """验证配置文件的完整性 (适配新版结构)
        
        Returns:
            (是否有效, 错误信息列表)
        """
        if not self.has_config():
            return False, ["配置文件不存在"]
        
        try:
            config = self.load_config()
        except yaml.YAMLError as e:
            return False, [f"配置文件格式错误: {e}"]
        
        errors = []
        
        # 1. 检查顶级必需键
        # 新版: ["project_name", "server", "environments"]
        required_top_keys = ["project_name", "server", "environments"]
        for key in required_top_keys:
            if key not in config:
                errors.append(f"缺少必需的顶级配置节: {key}")
        
        # 如果顶级配置缺失，后续检查可能会报错，先判断一下
        if errors:
            return False, errors

        # 2. 检查 server 配置
        if "server" in config:
            server = config["server"]
            if not isinstance(server, dict):
                errors.append("server 配置必须是一个对象(Dictionary)")
            else:
                # 必填项: host, user, repo_path
                # 选填项: port, key_file (不做强制检查)
                req_server_fields = ["host", "user", "repo_path"]
                for field in req_server_fields:
                    if field not in server:
                        errors.append(f"server 配置缺少必需项: {field}")

        # 3. 检查 environments 配置
        if "environments" in config:
            envs = config["environments"]
            if not isinstance(envs, dict):
                errors.append("environments 配置必须是一个对象(Dictionary)")
            elif len(envs) == 0:
                errors.append("environments 不能为空，至少需定义一个环境")
            else:
                # 遍历每个环境 (prod, test, dev...)
                for env_name, env_conf in envs.items():
                    if not isinstance(env_conf, dict):
                        errors.append(f"环境 '{env_name}' 的配置格式错误")
                        continue
                    
                    # 3.1 检查 deploy_path
                    if "deploy_path" not in env_conf:
                        errors.append(f"环境 '{env_name}' 缺少必需项: deploy_path")
                    
                    # 3.2 检查 steps
                    if "steps" not in env_conf:
                        errors.append(f"环境 '{env_name}' 缺少必需项: steps")
                    else:
                        steps = env_conf["steps"]
                        # 允许 steps 为 None (yaml中写了 steps: 但没内容) 或 空列表
                        if steps is None:
                            continue 
                            
                        if not isinstance(steps, list):
                            errors.append(f"环境 '{env_name}' 的 steps 必须是一个列表")
                        else:
                            # 3.3 检查 steps 里的每一项格式
                            for i, step in enumerate(steps):
                                # step 必须是 字符串 (Shell命令) 或 字典 (Action)
                                if isinstance(step, str):
                                    continue
                                elif isinstance(step, dict):
                                    if "action" not in step:
                                        errors.append(f"环境 '{env_name}' 的第 {i+1} 个步骤是字典，但缺少 'action' 键")
                                else:
                                    errors.append(f"环境 '{env_name}' 的第 {i+1} 个步骤格式无效 (必须是字符串或 Action 对象)")

        return len(errors) == 0, errors
