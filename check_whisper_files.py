import os
import json

def check_whisper_files():
    """
    检查Whisper文件是否已正确下载和配置
    """
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 检查vocab.bpe文件
    vocab_path = os.path.join(current_dir, "vocab.bpe")
    if os.path.exists(vocab_path):
        vocab_size = os.path.getsize(vocab_path) / 1024  # KB
        print(f"✓ vocab.bpe 文件已存在: {vocab_path}")
        print(f"  文件大小: {vocab_size:.2f} KB")
        
        # 检查文件内容
        try:
            with open(vocab_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"  行数: {len(lines)}")
                print(f"  前5行: {lines[:5]}")
        except Exception as e:
            print(f"  读取文件时出错: {e}")
    else:
        print(f"✗ vocab.bpe 文件不存在: {vocab_path}")
    
    print()
    
    # 检查encoder.json文件
    encoder_path = os.path.join(current_dir, "encoder.json")
    if os.path.exists(encoder_path):
        encoder_size = os.path.getsize(encoder_path) / 1024  # KB
        print(f"✓ encoder.json 文件已存在: {encoder_path}")
        print(f"  文件大小: {encoder_size:.2f} KB")
        
        # 检查文件内容
        try:
            with open(encoder_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"  包含 {len(data)} 个键值对")
                print(f"  示例键值对: {list(data.items())[:3]}")
        except Exception as e:
            print(f"  读取文件时出错: {e}")
    else:
        print(f"✗ encoder.json 文件不存在: {encoder_path}")
    
    print()
    
    # 检查tiktoken_ext.openai_public模块
    try:
        import tiktoken_ext.openai_public
        module_path = tiktoken_ext.openai_public.__file__
        print(f"✓ tiktoken_ext.openai_public 模块已存在: {module_path}")
        
        # 读取模块内容
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已更新URL
        if "https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe" in content:
            print("✗ tiktoken_ext.openai_public.py 文件中的URL尚未更新为本地文件路径")
        else:
            print("✓ tiktoken_ext.openai_public.py 文件中的URL已更新为本地文件路径")
    except ImportError:
        print("✗ tiktoken_ext.openai_public 模块不存在，请安装tiktoken库")
    except Exception as e:
        print(f"✗ 检查tiktoken_ext.openai_public模块时出错: {e}")
    
    print("\n总结:")
    if os.path.exists(vocab_path) and os.path.exists(encoder_path):
        print("✓ Whisper文件已正确下载")
        
        try:
            import tiktoken_ext.openai_public
            if "https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe" not in content:
                print("✓ tiktoken_ext.openai_public.py文件已正确配置")
                print("\n您现在可以使用本地Whisper模型了！")
            else:
                print("✗ tiktoken_ext.openai_public.py文件尚未正确配置")
                print("\n请运行 update_tiktoken_paths.py 脚本来更新tiktoken_ext.openai_public.py文件中的URL")
        except:
            print("✗ tiktoken_ext.openai_public模块不存在或无法访问")
            print("\n请安装tiktoken库，然后运行 update_tiktoken_paths.py 脚本")
    else:
        print("✗ Whisper文件尚未正确下载")
        print("\n请运行 download_whisper_files.py 脚本来下载Whisper文件")

if __name__ == "__main__":
    check_whisper_files() 