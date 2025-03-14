import os
import requests
import argparse

def download_file(url, output_path):
    """
    下载文件并保存到指定路径
    
    参数:
        url (str): 文件URL
        output_path (str): 输出文件路径
    
    返回:
        bool: 下载是否成功
    """
    try:
        print(f"正在下载: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 写入文件
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"文件已下载到: {output_path}")
        return True
    
    except Exception as e:
        print(f"下载文件时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="下载Whisper的vocab.bpe和encoder.json文件")
    parser.add_argument("--output_dir", "-o", default=None, 
                        help="输出目录路径，默认为当前目录")
    args = parser.parse_args()
    
    # 设置输出目录
    if args.output_dir:
        output_dir = args.output_dir
    else:
        # 默认使用当前目录
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 文件URL
    vocab_url = "https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe"
    encoder_url = "https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/encoder.json"
    
    # 输出文件路径
    vocab_path = os.path.join(output_dir, "vocab.bpe")
    encoder_path = os.path.join(output_dir, "encoder.json")
    
    # 下载文件
    vocab_success = download_file(vocab_url, vocab_path)
    encoder_success = download_file(encoder_url, encoder_path)
    
    if vocab_success and encoder_success:
        print("\n下载成功!")
        print(f"vocab.bpe: {vocab_path}")
        print(f"encoder.json: {encoder_path}")
        print("\n现在您可以使用这些文件运行Whisper模型了。")
    else:
        print("\n下载失败，请检查错误信息并重试。")

if __name__ == "__main__":
    main() 