import os
import sys
import importlib.util
import tiktoken_ext.openai_public

def update_tiktoken_paths():
    """
    更新tiktoken_ext.openai_public.py文件中的URL为本地文件路径
    """
    try:
        # 获取tiktoken_ext.openai_public模块的路径
        module_path = tiktoken_ext.openai_public.__file__
        print(f"tiktoken_ext.openai_public模块路径: {module_path}")
        
        # 读取模块内容
        with open(module_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 获取当前目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        vocab_path = os.path.join(current_dir, "vocab.bpe")
        encoder_path = os.path.join(current_dir, "encoder.json")
        
        # 检查文件是否存在
        if not os.path.exists(vocab_path):
            print(f"错误: vocab.bpe文件不存在: {vocab_path}")
            return False
        
        if not os.path.exists(encoder_path):
            print(f"错误: encoder.json文件不存在: {encoder_path}")
            return False
        
        print(f"使用本地文件:")
        print(f"  vocab.bpe: {vocab_path}")
        print(f"  encoder.json: {encoder_path}")
        
        # 替换URL为本地文件路径
        vocab_path_escaped = vocab_path.replace("\\", "/")
        encoder_path_escaped = encoder_path.replace("\\", "/")
        
        # 替换gpt2函数中的URL
        new_content = content.replace(
            'vocab_bpe_file="https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/vocab.bpe"',
            f'vocab_bpe_file="{vocab_path_escaped}"'
        )
        new_content = new_content.replace(
            'encoder_json_file="https://openaipublic.blob.core.windows.net/gpt-2/encodings/main/encoder.json"',
            f'encoder_json_file="{encoder_path_escaped}"'
        )
        
        # 写回修改后的内容
        with open(module_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("成功更新tiktoken_ext.openai_public.py文件中的URL为本地文件路径")
        
        # 重新加载模块
        spec = importlib.util.spec_from_file_location("tiktoken_ext.openai_public", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["tiktoken_ext.openai_public"] = module
        spec.loader.exec_module(module)
        
        return True
    
    except Exception as e:
        print(f"更新tiktoken_ext.openai_public.py文件时出错: {e}")
        return False

if __name__ == "__main__":
    success = update_tiktoken_paths()
    if success:
        print("\n更新成功！现在您可以使用本地Whisper模型了。")
    else:
        print("\n更新失败，请检查错误信息并重试。") 