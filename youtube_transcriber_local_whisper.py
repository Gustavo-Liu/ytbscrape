import os
import argparse
import yt_dlp
import ffmpeg
import math
import torch
import whisper
import time
import sys
from tqdm import tqdm

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

def setup_tiktoken_files():
    """
    设置tiktoken文件路径，指向本地的vocab.bpe和encoder.json文件
    """
    try:
        import tiktoken_ext.openai_public
        import importlib.util
        import sys
        
        # 获取tiktoken_ext.openai_public模块的路径
        module_path = tiktoken_ext.openai_public.__file__
        print(f"tiktoken_ext.openai_public模块路径: {module_path}")
        
        # 读取模块内容
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换URL为本地文件路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        vocab_path = os.path.join(current_dir, "vocab.bpe")
        encoder_path = os.path.join(current_dir, "encoder.json")
        
        # 检查文件是否存在
        if not os.path.exists(vocab_path) or not os.path.exists(encoder_path):
            print(f"警告: 本地vocab.bpe或encoder.json文件不存在")
            print(f"预期路径: {vocab_path}, {encoder_path}")
            return False
        
        # 替换文件路径
        new_content = content.replace(
            'vocab_bpe_file="https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe"',
            f'vocab_bpe_file="{vocab_path.replace(os.sep, "/")}"'
        )
        new_content = new_content.replace(
            'encoder_json_file="https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/encoder.json"',
            f'encoder_json_file="{encoder_path.replace(os.sep, "/")}"'
        )
        
        # 写回修改后的内容
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # 重新加载模块
        spec = importlib.util.spec_from_file_location("tiktoken_ext.openai_public", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["tiktoken_ext.openai_public"] = module
        spec.loader.exec_module(module)
        
        print("成功设置tiktoken文件路径")
        return True
    
    except Exception as e:
        print(f"设置tiktoken文件路径时出错: {e}")
        return False

def check_gpu_availability():
    """
    检查GPU是否可用，并显示详细信息
    
    返回:
        tuple: (是否可用CUDA, 是否可用MPS, 设备名称)
    """
    cuda_available = torch.cuda.is_available()
    mps_available = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    
    if cuda_available:
        device = "cuda"
        gpu_count = torch.cuda.device_count()
        gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
        
        print(f"检测到 {gpu_count} 个CUDA GPU:")
        for i, name in enumerate(gpu_names):
            memory_allocated = torch.cuda.memory_allocated(i) / (1024 ** 3)  # GB
            memory_reserved = torch.cuda.memory_reserved(i) / (1024 ** 3)    # GB
            print(f"  GPU {i}: {name}")
            print(f"    已分配内存: {memory_allocated:.2f} GB")
            print(f"    已保留内存: {memory_reserved:.2f} GB")
        
        # 设置CUDA设备属性以优化性能
        for i in range(gpu_count):
            torch.cuda.set_device(i)
            torch.cuda.empty_cache()
    
    elif mps_available:
        device = "mps"  # Apple Silicon GPU
        print("检测到 Apple Silicon GPU (MPS)")
    else:
        device = "cpu"
        print("未检测到GPU，将使用CPU")
    
    return cuda_available, mps_available, device

def load_local_whisper_model(model_path="small.pt", force_cpu=False):
    """
    加载本地Whisper模型
    
    参数:
        model_path (str): 模型文件路径
        force_cpu (bool): 是否强制使用CPU，即使GPU可用
    
    返回:
        whisper.model: 加载的Whisper模型
    """
    try:
        print(f"正在加载本地Whisper模型: {model_path}")
        
        # 设置tiktoken文件路径
        setup_tiktoken_files()
        
        # 检查GPU是否可用
        cuda_available, mps_available, device = check_gpu_availability()
        
        # 如果强制使用CPU，则忽略GPU
        if force_cpu:
            device = "cpu"
            print("已强制使用CPU")
        
        # 设置数据类型
        if device == "cuda":
            torch_dtype = torch.float16  # 半精度浮点数，在GPU上更快
        else:
            torch_dtype = torch.float32  # 单精度浮点数，在CPU上必须使用
        
        print(f"使用设备: {device}, 数据类型: {torch_dtype}")
        
        # 使用tqdm显示模型加载进度
        print("开始加载模型...")
        with tqdm(total=100, desc="加载模型", unit="%") as pbar:
            # 更新进度到10%
            pbar.update(10)
            
            # 加载模型
            model = whisper.load_model(model_path)
            
            # 更新进度到50%
            pbar.update(40)
            
            # 将模型移动到指定设备
            model.to(device)
            
            # 如果使用CUDA，尝试进一步优化
            if device == "cuda":
                # 使用torch.compile加速模型（仅在PyTorch 2.0+中可用）
                if hasattr(torch, 'compile') and callable(getattr(torch, 'compile')):
                    try:
                        print("正在使用torch.compile优化模型...")
                        model = torch.compile(model)
                    except Exception as e:
                        print(f"torch.compile优化失败: {e}")
            
            # 完成加载
            pbar.update(100 - pbar.n)
        
        print("模型加载成功")
        return model, device
    
    except Exception as e:
        print(f"加载模型时出错: {e}")
        return None, "cpu"

def transcribe_audio_with_local_whisper(audio_file, model_info, output_path=".", language="zh"):
    """
    使用本地Whisper模型转录音频
    
    参数:
        audio_file (str): 音频文件路径
        model_info: (model, device) 元组，包含模型和设备信息
        output_path (str): 输出目录路径
        language (str): 音频语言代码
    
    返回:
        str: 转录文本的文件路径
    """
    try:
        model, device = model_info
        print(f"正在使用本地Whisper模型转录音频: {audio_file}")
        print(f"使用设备: {device}")
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        
        # 获取文件名（不带扩展名）
        base_name = os.path.splitext(os.path.basename(audio_file))[0]
        text_file = os.path.join(output_path, f"{base_name}_local.txt")
        
        # 获取音频时长
        try:
            probe = ffmpeg.probe(audio_file)
            duration = float(probe['format']['duration'])
            print(f"音频时长: {duration:.2f}秒")
        except Exception as e:
            print(f"获取音频时长时出错: {e}")
            duration = 600  # 默认10分钟
        
        # 转录选项
        options = {
            "language": language,
            "task": "transcribe",
            "verbose": False,  # 关闭详细输出，以免干扰进度条
            "word_timestamps": True,
            "beam_size": 5,    # 增加beam search大小以提高准确性
            "best_of": 5       # 增加候选数量以提高准确性
        }
        
        # 如果使用GPU，添加批处理选项以加速
        if device == "cuda":
            options["batch_size"] = 16  # 增加批处理大小以利用GPU并行性
        
        # 转录
        print("开始转录...")
        
        # 创建进度条
        pbar = tqdm(total=100, desc="转录进度", unit="%")
        
        # 记录开始时间
        start_time = time.time()
        
        # 转录音频
        result = model.transcribe(audio_file, **options)
        
        # 更新进度条到100%
        pbar.update(100 - pbar.n)
        pbar.close()
        
        # 计算转录时间
        elapsed_time = time.time() - start_time
        print(f"转录完成，耗时: {elapsed_time:.2f}秒")
        
        # 计算实时因子（处理时间与音频时长的比率）
        rtf = elapsed_time / duration
        print(f"实时因子(RTF): {rtf:.2f}x (RTF < 1 表示比实时快)")
        
        # 将转录文本写入文件
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(result["text"])
        
        # 打印转录结果的一部分
        print("\n转录结果预览:")
        preview_length = min(200, len(result["text"]))
        print(result["text"][:preview_length] + "..." if len(result["text"]) > preview_length else result["text"])
        
        print(f"\n转录已保存到: {text_file}")
        return text_file
    
    except Exception as e:
        print(f"转录音频时出错: {e}")
        return None

def format_transcript(input_file, output_file=None):
    """
    格式化转录文本，添加适当的换行
    
    参数:
        input_file (str): 输入文件路径
        output_file (str): 输出文件路径，如果为None，则生成新的文件名
    """
    try:
        # 读取文件内容
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 如果没有指定输出文件，则生成新的文件名
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_格式化.txt"
        
        # 在标点符号后添加换行符
        formatted_content = content
        for punct in ["。", "！", "？", ".", "!", "?"]:
            formatted_content = formatted_content.replace(punct, punct + "\n")
        
        # 将格式化后的文本写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
        print(f"文本已格式化并保存到: {output_file}")
        return output_file
    
    except Exception as e:
        print(f"格式化文本时出错: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="下载YouTube视频并使用本地Whisper模型转录为文本")
    parser.add_argument("url", help="YouTube视频URL")
    parser.add_argument("--output", "-o", default="output", help="输出目录路径")
    parser.add_argument("--model", "-m", default="small.pt", help="Whisper模型文件路径")
    parser.add_argument("--language", "-l", default="zh", help="音频语言代码，默认为中文(zh)")
    parser.add_argument("--format", "-f", action="store_true", help="是否格式化转录文本")
    parser.add_argument("--force-cpu", action="store_true", help="强制使用CPU，即使GPU可用")
    parser.add_argument("--skip-download", "-s", action="store_true", help="跳过下载视频，直接使用已有的音频文件")
    parser.add_argument("--audio-file", "-a", help="直接指定音频文件路径，跳过视频下载和音频提取")
    args = parser.parse_args()
    
    # 获取音频文件
    audio_file = None
    video_file = None
    
    if args.audio_file:
        # 直接使用指定的音频文件
        audio_file = args.audio_file
        if not os.path.exists(audio_file):
            print(f"错误: 指定的音频文件不存在: {audio_file}")
            return
    elif not args.skip_download:
        # 下载视频
        video_file = download_youtube_video(args.url, args.output)
        if not video_file:
            return
        
        # 提取音频
        audio_file = extract_audio(video_file, args.output)
        if not audio_file:
            return
    else:
        # 尝试查找已有的音频文件
        if not os.path.exists(args.output):
            print(f"错误: 输出目录不存在: {args.output}")
            return
        
        # 从URL中提取视频ID
        try:
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(args.url)
            video_id = parse_qs(parsed_url.query).get('v', [None])[0]
            if not video_id:
                print("错误: 无法从URL中提取视频ID")
                return
            
            # 查找包含视频ID的音频文件
            for file in os.listdir(args.output):
                if file.endswith(".mp3") and video_id in file:
                    audio_file = os.path.join(args.output, file)
                    print(f"找到已有的音频文件: {audio_file}")
                    break
            
            if not audio_file:
                print(f"错误: 未找到包含视频ID {video_id} 的音频文件")
                return
        except Exception as e:
            print(f"查找已有音频文件时出错: {e}")
            return
    
    # 加载模型
    model_info = load_local_whisper_model(args.model, args.force_cpu)
    if not model_info[0]:  # model是元组的第一个元素
        return
    
    # 转录音频
    text_file = transcribe_audio_with_local_whisper(audio_file, model_info, args.output, args.language)
    if not text_file:
        return
    
    # 格式化转录文本
    if args.format:
        formatted_file = format_transcript(text_file)
        if formatted_file:
            print(f"格式化文本: {formatted_file}")
    
    print("处理完成!")
    if video_file:
        print(f"视频: {video_file}")
    print(f"音频: {audio_file}")
    print(f"文本: {text_file}")

if __name__ == "__main__":
    main() 