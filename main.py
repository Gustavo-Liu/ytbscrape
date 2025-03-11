import os
import sys
import argparse
from datetime import datetime
import re
import json

def download_audio(url, output_path="downloads"):
    """
    从YouTube URL下载音频
    """
    try:
        # 创建下载目录
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        print(f"正在处理URL: {url}")
        
        # 确保URL格式正确
        if "youtube.com/watch?v=" not in url and "youtu.be/" not in url:
            print(f"无效的YouTube URL: {url}")
            return None, None
            
        # 提取视频ID
        video_id = None
        if "youtube.com/watch?v=" in url:
            video_id = url.split("youtube.com/watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            video_id = url.split("youtu.be/")[1].split("?")[0]
            
        if not video_id:
            print("无法提取视频ID")
            return None, None
            
        print(f"视频ID: {video_id}")
        
        # 使用视频ID构建新的URL
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"使用清理后的URL: {clean_url}")
        
        # 使用 yt-dlp 下载音频
        import yt_dlp
        
        # 设置下载选项
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_path, f"audio_{timestamp}")
        
        # 检查是否有 FFmpeg
        import shutil
        has_ffmpeg = shutil.which('ffmpeg') is not None
        
        if has_ffmpeg:
            print("检测到 FFmpeg，将转换为 MP3 格式")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_file,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
                'ignoreerrors': False,
            }
        else:
            print("未检测到 FFmpeg，将下载原始音频格式")
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_file + '.%(ext)s',
                'quiet': False,
                'no_warnings': False,
                'ignoreerrors': False,
            }
        
        # 获取视频信息
        print("获取视频信息...")
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            try:
                info = ydl.extract_info(clean_url, download=False)
                title = info.get('title', '未知标题')
                print(f"视频标题: {title}")
            except Exception as e:
                print(f"获取视频信息失败: {str(e)}")
                title = "未知标题"
        
        # 下载音频
        print("开始下载音频...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_url])
        
        # 查找下载的文件
        print("查找下载的音频文件...")
        downloaded_file = None
        for file in os.listdir(output_path):
            if file.startswith(os.path.basename(output_file)):
                downloaded_file = os.path.join(output_path, file)
                print(f"找到音频文件: {downloaded_file}")
                break
        
        if downloaded_file:
            return downloaded_file, title
        else:
            print("找不到下载的音频文件")
            return None, None
        
    except Exception as e:
        print(f"下载出错: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        return None, None

def transcribe_audio(audio_file):
    """
    使用本地语音识别模型将音频转换为文本
    """
    try:
        print("准备转录音频...")
        
        # 检查文件是否存在
        if not os.path.exists(audio_file):
            print(f"音频文件不存在: {audio_file}")
            return None
            
        print(f"音频文件大小: {os.path.getsize(audio_file) / (1024*1024):.2f} MB")
        
        # 检查 FFmpeg 是否可用
        import shutil
        
        # 首先检查当前目录或项目目录中是否有静态版本的 FFmpeg
        ffmpeg_path = None
        possible_paths = [
            './ffmpeg',                    # 当前目录
            './bin/ffmpeg',                # bin 子目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg'),  # 脚本所在目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bin/ffmpeg')  # 脚本所在目录的 bin 子目录
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                ffmpeg_path = path
                print(f"找到本地 FFmpeg: {ffmpeg_path}")
                break
        
        # 如果没有找到本地版本，检查系统路径
        has_ffmpeg = shutil.which('ffmpeg') is not None
        if has_ffmpeg:
            ffmpeg_path = shutil.which('ffmpeg')
            print(f"使用系统 FFmpeg: {ffmpeg_path}")
        
        if not ffmpeg_path:
            print("警告: FFmpeg 不可用，Whisper 可能无法处理某些音频格式")
            print("尝试使用替代方法...")
            
            # 如果没有 FFmpeg，我们可以尝试直接提取文本
            print("尝试使用简单的文本提取方法...")
            return f"由于缺少 FFmpeg，无法转录音频。请安装 FFmpeg 后重试。\n\n视频 ID: {os.path.basename(audio_file).split('_')[1].split('.')[0]}\n文件大小: {os.path.getsize(audio_file) / (1024*1024):.2f} MB"
        
        # 尝试导入 whisper 模块
        try:
            import whisper
            
            # 如果找到了 FFmpeg，设置环境变量让 Whisper 使用它
            if ffmpeg_path:
                os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
                print(f"已将 {os.path.dirname(ffmpeg_path)} 添加到 PATH 环境变量")
            
            print("成功导入 whisper 模块")
        except ImportError:
            print("无法导入 whisper 模块，尝试安装...")
            try:
                import subprocess
                subprocess.run([sys.executable, '-m', 'pip', 'install', 'openai-whisper'], check=True)
                import whisper
                print("成功安装并导入 whisper 模块")
            except Exception as e:
                print(f"安装 whisper 失败: {str(e)}")
                return "无法加载语音识别模型。请手动安装 whisper: pip install openai-whisper"
        
        # 加载模型
        print("正在加载 Whisper 模型 (这可能需要一些时间)...")
        try:
            # 尝试加载较小的模型以加快速度
            model = whisper.load_model("tiny")
            print("已加载 'tiny' 模型")
        except Exception as e:
            print(f"加载 'tiny' 模型失败: {str(e)}")
            print("尝试加载 'base' 模型...")
            try:
                model = whisper.load_model("base")
                print("已加载 'base' 模型")
            except Exception as e:
                print(f"加载 'base' 模型失败: {str(e)}")
                return None
        
        # 转录
        print("正在转录音频 (这可能需要几分钟时间)...")
        
        # 如果有 FFmpeg 路径，确保 Whisper 能找到它
        if ffmpeg_path:
            # 保存原始 PATH
            original_path = os.environ.get("PATH", "")
            # 临时修改 PATH 环境变量
            os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + original_path
            print(f"临时设置 PATH 环境变量以包含 FFmpeg 目录")
        
        # 设置 Whisper 选项，禁用 FFmpeg 相关功能
        try:
            # 尝试使用自定义设置
            result = model.transcribe(
                audio_file,
                fp16=False,  # 在 CPU 上使用 FP32
                language="auto",  # 自动检测语言
            )
        except Exception as e:
            print(f"使用自定义设置转录失败: {str(e)}")
            print("尝试使用默认设置...")
            try:
                result = model.transcribe(audio_file)
            except Exception as e:
                print(f"使用默认设置转录也失败: {str(e)}")
                return f"转录失败。错误: {str(e)}"
        
        # 如果修改了 PATH，恢复原始值
        if ffmpeg_path and 'original_path' in locals():
            os.environ["PATH"] = original_path
            print("已恢复原始 PATH 环境变量")
        
        return result["text"]
        
    except Exception as e:
        print(f"转录出错: {str(e)}")
        print(f"错误类型: {type(e).__name__}")
        return None

def generate_report(title, text, output_path="reports"):
    """
    生成报告
    """
    try:
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(output_path, f"report_{timestamp}.txt")
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(f"视频标题: {title}\n")
            f.write("=" * 50 + "\n\n")
            f.write("转录内容:\n")
            f.write("-" * 50 + "\n")
            f.write(text)
            
        return report_file
        
    except Exception as e:
        print(f"生成报告出错: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description="YouTube视频转文本工具")
    parser.add_argument("url", help="YouTube视频URL")
    parser.add_argument("--skip-download", action="store_true", help="跳过下载步骤，使用已有的音频文件")
    parser.add_argument("--audio-file", help="指定要使用的音频文件路径")
    args = parser.parse_args()
    
    audio_file = None
    video_title = "未知视频"
    
    # 1. 下载音频（除非指定跳过）
    if not args.skip_download:
        print("步骤1: 下载音频")
        audio_file, video_title = download_audio(args.url)
        if not audio_file:
            print("下载失败，退出程序")
            sys.exit(1)
    else:
        print("跳过下载步骤")
        if args.audio_file and os.path.exists(args.audio_file):
            audio_file = args.audio_file
            print(f"使用指定的音频文件: {audio_file}")
        else:
            print("未指定有效的音频文件")
            sys.exit(1)
        
    # 2. 转录音频
    print("\n步骤2: 转录音频")
    text = transcribe_audio(audio_file)
    if not text:
        print("转录失败，退出程序")
        sys.exit(1)
        
    # 3. 生成报告
    print("\n步骤3: 生成报告")
    report_file = generate_report(video_title, text)
    if report_file:
        print(f"\n报告已生成: {report_file}")
        # 打开报告文件
        try:
            with open(report_file, "r", encoding="utf-8") as f:
                print("\n报告预览:")
                print("-" * 50)
                print(f.read(500) + "...")  # 只显示前500个字符
                print("-" * 50)
        except Exception as e:
            print(f"无法预览报告: {str(e)}")
    
    # 4. 清理音频文件（除非指定跳过）
    if not args.skip_download and audio_file and os.path.exists(audio_file):
        os.remove(audio_file)
        print("临时音频文件已清理")

if __name__ == "__main__":
    main() 