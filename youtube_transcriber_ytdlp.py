import os
import argparse
import yt_dlp
import ffmpeg
import math
from openai import OpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化OpenAI客户端
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def download_youtube_video(url, output_path="."):
    """
    使用yt-dlp下载YouTube视频
    
    参数:
        url (str): YouTube视频URL
        output_path (str): 输出目录路径
    
    返回:
        str: 下载的视频文件路径
    """
    try:
        print(f"正在下载视频: {url}")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 设置yt-dlp选项
        ydl_opts = {
            'format': 'best[ext=mp4]',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 60,  # 增加超时时间到60秒
            'retries': 10,         # 增加重试次数
            'fragment_retries': 10 # 增加片段重试次数
        }
        
        # 下载视频
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info)
        
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

def get_audio_duration(audio_file):
    """
    获取音频文件的时长（秒）
    
    参数:
        audio_file (str): 音频文件路径
    
    返回:
        float: 音频时长（秒）
    """
    try:
        probe = ffmpeg.probe(audio_file)
        duration = float(probe['format']['duration'])
        return duration
    except Exception as e:
        print(f"获取音频时长时出错: {e}")
        return 0

def split_audio(audio_file, output_path=".", segment_length=600):
    """
    将音频文件分割成多个小段
    
    参数:
        audio_file (str): 音频文件路径
        output_path (str): 输出目录路径
        segment_length (int): 每段音频的长度（秒）
    
    返回:
        list: 分割后的音频文件路径列表
    """
    try:
        print(f"正在分割音频: {audio_file}")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 获取文件名（不带扩展名）
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        
        # 获取音频时长
        duration = get_audio_duration(audio_file)
        
        # 如果音频时长小于分段长度，直接返回原音频
        if duration <= segment_length:
            return [audio_file]
        
        # 计算需要分割的段数
        num_segments = math.ceil(duration / segment_length)
        
        # 分割音频
        segment_files = []
        for i in range(num_segments):
            start_time = i * segment_length
            segment_file = os.path.join(output_path, f"{base_name}_part{i+1}.mp3")
            
            # 使用ffmpeg分割音频
            (
                ffmpeg
                .input(audio_file, ss=start_time, t=segment_length)
                .output(segment_file, acodec='libmp3lame', ab='128k')
                .run(overwrite_output=True, quiet=True)
            )
            
            segment_files.append(segment_file)
            print(f"已分割音频片段 {i+1}/{num_segments}: {segment_file}")
        
        return segment_files
    
    except Exception as e:
        print(f"分割音频时出错: {e}")
        return [audio_file]  # 出错时返回原音频

def transcribe_audio_segment(audio_file, output_path="."):
    """
    使用OpenAI的Whisper API转录单个音频片段
    
    参数:
        audio_file (str): 音频文件路径
        output_path (str): 输出目录路径
    
    返回:
        str: 转录文本
    """
    try:
        print(f"正在转录音频片段: {audio_file}")
        
        # 打开音频文件
        with open(audio_file, "rb") as audio:
            # 使用OpenAI的Whisper API进行转录
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                response_format="verbose_json"  # 使用详细JSON格式获取更多信息
            )
        
        # 返回转录文本
        return transcript.text
    
    except Exception as e:
        print(f"转录音频片段时出错: {e}")
        return ""

def format_transcript(text):
    """
    格式化转录文本，添加适当的换行
    
    参数:
        text (str): 原始转录文本
    
    返回:
        str: 格式化后的文本
    """
    # 替换常见的标点符号为带空格的版本，以便于分割
    text = text.replace("。", "。 ")
    text = text.replace("？", "？ ")
    text = text.replace("！", "！ ")
    text = text.replace("，", "， ")
    text = text.replace("；", "； ")
    text = text.replace("：", "： ")
    
    # 按空格分割文本
    words = text.split()
    
    # 每15-20个词组成一个段落
    paragraphs = []
    current_paragraph = []
    
    for word in words:
        current_paragraph.append(word)
        # 如果当前词以句号、问号或感叹号结尾，并且段落长度超过15个词，则结束当前段落
        if (word.endswith("。") or word.endswith("？") or word.endswith("！") or 
            word.endswith(".") or word.endswith("?") or word.endswith("!")) and len(current_paragraph) >= 15:
            paragraphs.append(" ".join(current_paragraph))
            current_paragraph = []
    
    # 处理最后一个段落
    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))
    
    # 返回格式化后的文本
    return "\n\n".join(paragraphs)

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
        
        # 分割音频
        segment_files = split_audio(audio_file, output_path)
        
        # 转录每个音频片段
        transcript_parts = []
        for segment_file in segment_files:
            transcript_part = transcribe_audio_segment(segment_file, output_path)
            transcript_parts.append(transcript_part)
        
        # 合并所有转录文本
        full_transcript = " ".join(transcript_parts)
        
        # 格式化转录文本
        formatted_transcript = format_transcript(full_transcript)
        
        # 将转录文本写入文件
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(formatted_transcript)
        
        print(f"转录已保存到: {text_file}")
        
        # 如果创建了临时分段文件，删除它们
        if len(segment_files) > 1 and segment_files[0] != audio_file:
            for segment_file in segment_files:
                if os.path.exists(segment_file) and segment_file != audio_file:
                    os.remove(segment_file)
            print("临时音频片段已删除")
        
        return text_file
    
    except Exception as e:
        print(f"转录音频时出错: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="下载YouTube视频并转录为文本")
    parser.add_argument("url", help="YouTube视频URL")
    parser.add_argument("--output", "-o", default="output", help="输出目录路径")
    parser.add_argument("--segment-length", "-s", type=int, default=600, help="音频分段长度（秒），默认为600秒（10分钟）")
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