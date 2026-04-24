#!/usr/bin/env python3
"""
DigiHuman 服务启动脚本
一次性启动前端和后端服务
"""
import os
import subprocess
import time
import sys

def print_banner():
    """打印启动横幅"""
    print("=" * 40)
    print("DigiHuman 服务启动脚本")
    print("=" * 40)

def start_backend():
    """启动后端服务"""
    print("\n启动后端服务...")
    # 启动后端服务，创建新的命令窗口
    if sys.platform == 'win32':
        # Windows系统
        subprocess.Popen([
            'cmd.exe', '/c', 'start', 'cmd.exe', '/k', 
            'python run_server.py'
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
    else:
        # Linux/Mac系统
        subprocess.Popen([
            'gnome-terminal', '--', 'python', 'run_server.py'
        ], cwd=os.path.dirname(os.path.abspath(__file__)))

def start_frontend():
    """启动前端服务"""
    print("\n启动前端服务...")
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    if sys.platform == 'win32':
        # Windows系统
        subprocess.Popen([
            'cmd.exe', '/c', 'start', 'cmd.exe', '/k', 
            'npm run dev'
        ], cwd=frontend_dir)
    else:
        # Linux/Mac系统
        subprocess.Popen([
            'gnome-terminal', '--', 'npm', 'run', 'dev'
        ], cwd=frontend_dir)

def main():
    """主函数"""
    print_banner()
    
    # 启动后端服务
    start_backend()
    
    # 等待后端服务启动
    print("等待后端服务启动...")
    time.sleep(5)
    
    # 启动前端服务
    start_frontend()
    
    print("\n" + "=" * 40)
    print("服务启动完成！")
    print("=" * 40)
    print("后端服务地址: http://localhost:8001")
    print("前端服务地址: http://localhost:3000")
    print("=" * 40)
    print("按任意键退出...")
    input()

if __name__ == "__main__":
    main()
