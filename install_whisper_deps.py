import subprocess
import sys
import os

def install_dependencies():
    """安装Whisper所需的依赖项"""
    print("正在安装Whisper所需的依赖项...")
    
    # 安装FFmpeg相关库
    print("正在安装FFmpeg相关库...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ffmpeg-python"])
    
    # 安装yt-dlp
    print("正在安装yt-dlp...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
    
    # 安装PyTorch
    print("正在安装PyTorch...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "torch"])
    
    # 安装transformers和datasets
    print("正在安装transformers和datasets...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers", "datasets"])
    
    print("所有依赖项安装完成！")

if __name__ == "__main__":
    install_dependencies() 