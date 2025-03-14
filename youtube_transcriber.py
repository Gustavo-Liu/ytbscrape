import os
import argparse
from pytube import YouTube
import ffmpeg
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def download_youtube_video(url, output_path="."):
    """
    下载YouTube视频
    
    参数:
        url (str): YouTube视频URL
        output_path (str): 输出目录路径
    
    返回:
        str: 下载的视频文件路径
    """
    try:
        print(f"正在下载视频: {url}")
        yt = YouTube(url)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 下载视频
        video_file = video.download(output_path)
        print(f"视频已下载到: {video_file}")
        return video_file
    
    except Exception as e:
        print(f"下载视频时出错: {e}")
        return None

def extract_audio(video_file, output_path="."):
    """
    从视频文件中提取音频
    
    参数:
        video_file (str): 视频文件路径
        output_path (str): 输出目录路径
    
    返回:
        str: 提取的音频文件路径
    """
    try:
        print(f"正在从视频中提取音频: {video_file}")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 获取文件名（不带扩展名）
        base_name = os.path.splitext(os.path.basename(video_file))[0]
        audio_file = os.path.join(output_path, f"{base_name}.mp3")
        
        # 使用ffmpeg提取音频
        (
            ffmpeg
            .input(video_file)
            .output(audio_file, acodec='libmp3lame', ab='128k')
            .run(overwrite_output=True, quiet=True)
        )
        
        print(f"音频已提取到: {audio_file}")
        return audio_file
    
    except Exception as e:
        print(f"提取音频时出错: {e}")
        return None

def transcribe_audio(audio_file, output_path="."):
    """
    使用OpenAI的Whisper API将音频转录为文本
    
    参数:
        audio_file (str): 音频文件路径
        output_path (str): 输出目录路径
    
    返回:
        str: 转录文本的文件路径
    """
    try:
        print(f"正在转录音频: {audio_file}")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 获取文件名（不带扩展名）
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        text_file = os.path.join(output_path, f"{base_name}.txt")
        
        # 打开音频文件
        with open(audio_file, "rb") as audio:
            # 使用OpenAI的Whisper API进行转录
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio
            )
        
        # 将转录文本写入文件
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(transcript.text)
        
        print(f"转录已保存到: {text_file}")
        return text_file
    
    except Exception as e:
        print(f"转录音频时出错: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="下载YouTube视频并转录为文本")
    parser.add_argument("url", help="YouTube视频URL")
    parser.add_argument("--output", "-o", default="output", help="输出目录路径")
    args = parser.parse_args()
    
    # 下载视频
    video_file = download_youtube_video(args.url, args.output)
    if not video_file:
        return
    
    # 提取音频
    audio_file = extract_audio(video_file, args.output)
    if not audio_file:
        return
    
    # 转录音频
    text_file = transcribe_audio(audio_file, args.output)
    if not text_file:
        return
    
    print("处理完成!")
    print(f"视频: {video_file}")
    print(f"音频: {audio_file}")
    print(f"文本: {text_file}")

if __name__ == "__main__":
    main() 