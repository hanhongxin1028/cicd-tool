import os
import glob
import subprocess
from typing import Dict, Any

def run(context: Dict[str, Any]) -> None:
    """
    Nginx 部署插件逻辑
    
    约定：
    1. 仅扫描项目根目录下的 ./nginx 文件夹
    2. 如果文件夹不存在或无配置文件，则静默跳过
    3. 如果存在，自动部署到 /etc/nginx/sites-available 并建立软链
    
    Args:
        context: 上下文变量 (包含 cwd, deploy_path 等)
    
    Raises:
        RuntimeError: Nginx 相关命令执行失败时抛出
    """
    
    # ==========================================
    # 1. 路径约定与检查
    # ==========================================
    # 强约定：配置必须放在项目根目录的 nginx 文件夹下
    local_conf_rel = "./nginx" 
    abs_local_dir = os.path.join(context['cwd'], local_conf_rel)
    
    sites_available = "/etc/nginx/sites-available"
    sites_enabled = "/etc/nginx/sites-enabled"

    # 检查源目录：如果项目里根本没建 nginx 目录，优雅退出，不视为错误
    if not os.path.exists(abs_local_dir):
        return

    # 查找所有 .conf 文件
    conf_files = glob.glob(os.path.join(abs_local_dir, "*.conf"))
    if not conf_files:
        return

    # ==========================================
    # 2. 执行部署操作
    # ==========================================
    try:
        # 
        # 流程：Local Config -> cp -> Available -> ln -> Enabled -> Reload
        print("🔒 正在请求 sudo 权限以配置 Nginx...")
        subprocess.run(["sudo", "-v"], check=True)

        for conf_file in conf_files:
            filename = os.path.basename(conf_file)
            target_path = os.path.join(sites_available, filename)
            link_path = os.path.join(sites_enabled, filename)
            
            # A. 复制配置文件 (覆盖模式)
            # sudo cp ./nginx/xxx.conf /etc/nginx/sites-available/xxx.conf
            subprocess.run(
                ["sudo", "cp", "-f", conf_file, target_path], 
                check=True
            )
            
            # B. 创建软链接 (强制模式)
            # sudo ln -sf /etc/nginx/sites-available/xxx.conf /etc/nginx/sites-enabled/xxx.conf
            subprocess.run(
                ["sudo", "ln", "-sf", target_path, link_path], 
                check=True
            )

        # ==========================================
        # 3. 校验与生效
        # ==========================================
        
        # C. 语法校验
        # sudo nginx -t
        subprocess.run(
            ["sudo", "nginx", "-t"], 
            check=True
        )
        
        # D. 平滑重载配置 (不中断现有连接)
        # sudo nginx -s reload
        subprocess.run(
            ["sudo", "nginx", "-s", "reload"], 
            check=True
        )

    except subprocess.CalledProcessError as e:
        # 捕获 subprocess 的错误输出 (stderr)
        err_msg = e.stderr.decode().strip() if e.stderr else str(e)
        
        # 抛出异常，交给上层 cmd_deploy.py 打印红色错误日志
        raise RuntimeError(f"Nginx 部署失败: {err_msg}")