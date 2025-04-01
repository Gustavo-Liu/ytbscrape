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

def download_youtube_video(url, output_path=".", cookies_file=None, audio_only=False):
    """
    使用yt-dlp下载视频或音频
    
    参数:
        url (str): 视频URL
        output_path (str): 输出目录路径
        cookies_file (str): cookies文件路径
        audio_only (bool): 是否只下载音频
    
    返回:
        str: 下载的文件路径
    """
    try:
        print(f"正在下载{'音频' if audio_only else '视频'}: {url}")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 设置yt-dlp选项
        ydl_opts = {
            'format': 'bestaudio/best' if audio_only else 'best[ext=mp4]',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
            'socket_timeout': 60,  # 增加超时时间到60秒
            'retries': 10,         # 增加重试次数
            'fragment_retries': 10, # 增加片段重试次数
            'extract_flat': True,  # 提取扁平化信息
            'extract_flat_in_playlist': True,  # 在播放列表中提取扁平化信息
            'format_sort': ['res', 'fps', 'codec', 'size', 'br', 'asr', 'ext'],  # 格式排序
            'prefer_free_formats': True,  # 优先选择免费格式
        }
        
        # 添加后处理器
        if audio_only:
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            expected_ext = 'mp3'
        else:
            ydl_opts.update({
                'merge_output_format': 'mp4',
            })
            expected_ext = 'mp4'
        
        # 如果提供了cookies文件，添加到选项中
        if cookies_file and os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
            print(f"使用cookies文件: {cookies_file}")
        
        # 如果是B站视频，添加特定的选项
        if 'bilibili.com' in url:
            if audio_only:
                ydl_opts.update({
                    'format': '30280',  # 最高质量音频
                })
            else:
                ydl_opts.update({
                    'format': '100048+30280',  # 720p视频 + 最高质量音频
                })
        
        # 下载文件
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # 修正文件扩展名
            if audio_only and not file_path.endswith('.mp3'):
                base_path = os.path.splitext(file_path)[0]
                file_path = f"{base_path}.{expected_ext}"
            
            # 确保文件存在
            if not os.path.exists(file_path):
                # 尝试查找实际文件
                base_path = os.path.splitext(file_path)[0]
                possible_paths = [
                    f"{base_path}.{expected_ext}",
                    f"{base_path}.{info.get('ext', expected_ext)}"
                ]
                
                for possible_path in possible_paths:
                    if os.path.exists(possible_path):
                        file_path = possible_path
                        break
        
        print(f"{'音频' if audio_only else '视频'}已下载到: {file_path}")
        
        # 再次确认文件是否存在
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"下载完成，但找不到文件: {file_path}")
            
        return file_path
    
    except Exception as e:
        print(f"下载{'音频' if audio_only else '视频'}时出错: {e}")
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
        
        # 检查文件是否存在
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
        # 打开音频文件
        with open(audio_file, "rb") as audio_data:
            # 使用OpenAI的Whisper API进行转录
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_data,
                response_format="text"  # 改为纯文本格式简化处理
            )
        
        # 由于response_format="text"，transcript是字符串，不需要再获取.text属性
        if isinstance(transcript, str):
            return transcript
        else:
            # 如果返回对象不是字符串，尝试获取text属性
            return getattr(transcript, 'text', str(transcript))
    
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
        
        # 检查音频文件是否存在
        if not os.path.exists(audio_file):
            raise FileNotFoundError(f"音频文件不存在: {audio_file}")
        
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
            if transcript_part:  # 确保转录内容不为空
                transcript_parts.append(transcript_part)
            else:
                print(f"警告: 片段 {segment_file} 转录内容为空")
        
        # 检查是否有转录内容
        if not transcript_parts:
            raise ValueError(f"无法转录任何音频片段，请检查音频文件格式和OpenAI API配置")
        
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
    parser = argparse.ArgumentParser(description="下载视频/音频并转录为文本")
    parser.add_argument("url", help="视频URL")
    parser.add_argument("--output", "-o", default="output", help="输出目录路径")
    parser.add_argument("--segment-length", "-s", type=int, default=600, help="音频分段长度（秒），默认为600秒（10分钟）")
    parser.add_argument("--cookies", "-c", help="cookies文件路径")
    parser.add_argument("--audio-only", "-a", action="store_true", help="只下载音频")
    args = parser.parse_args()
    
    # 下载视频/音频
    file_path = download_youtube_video(args.url, args.output, args.cookies, args.audio_only)
    if not file_path:
        return
    
    if args.audio_only:
        # 如果只下载音频，直接进行转录
        text_file = transcribe_audio(file_path, args.output)
    else:
        # 如果下载了视频，先提取音频再转录
        audio_file = extract_audio(file_path, args.output)
        if not audio_file:
            return
        text_file = transcribe_audio(audio_file, args.output)
    
    if not text_file:
        return
    
    print("处理完成!")
    print(f"{'音频' if args.audio_only else '视频'}: {file_path}")
    print(f"文本: {text_file}")

if __name__ == "__main__":
    main() 