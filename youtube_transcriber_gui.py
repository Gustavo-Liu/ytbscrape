import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, StringVar, IntVar, BooleanVar
from pathlib import Path

# 导入转录脚本的功能
from youtube_transcriber_ytdlp import (
    download_youtube_video,
    extract_audio,
    transcribe_audio
)

class YouTubeTranscriberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube视频转录工具")
        self.root.geometry("800x600")
        self.root.minsize(600, 450)
        
        # 创建样式
        self.style = ttk.Style()
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TButton", font=("Arial", 10))
        self.style.configure("TLabel", font=("Arial", 10), background="#f0f0f0")
        self.style.configure("Header.TLabel", font=("Arial", 12, "bold"), background="#f0f0f0")
        self.style.configure("TEntry", font=("Arial", 10))
        self.style.configure("TCheckbutton", font=("Arial", 10), background="#f0f0f0")
        
        # 设置变量
        self.url_var = StringVar()
        self.output_path_var = StringVar(value=os.path.join(os.getcwd(), "output"))
        self.cookies_path_var = StringVar()
        self.audio_only_var = BooleanVar(value=False)
        self.segment_length_var = IntVar(value=600)
        self.status_var = StringVar(value="准备就绪")
        self.progress_var = tk.DoubleVar(value=0.0)
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, style="TFrame", padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 添加组件
        self._create_widgets()
        
        # 日志区域
        self.create_log_area()
        
        # 状态栏
        self.create_status_bar()
        
    def _create_widgets(self):
        """创建所有GUI组件"""
        # URL输入区域
        url_frame = ttk.Frame(self.main_frame, style="TFrame")
        url_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(url_frame, text="YouTube视频URL:", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Entry(url_frame, textvariable=self.url_var, width=80).pack(fill=tk.X, pady=5)
        
        # 选项区域
        options_frame = ttk.Frame(self.main_frame, style="TFrame")
        options_frame.pack(fill=tk.X, pady=10)
        
        # 输出路径
        path_frame = ttk.Frame(options_frame, style="TFrame")
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="输出路径:", style="TLabel").pack(side=tk.LEFT)
        ttk.Entry(path_frame, textvariable=self.output_path_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览...", command=self.browse_output_path).pack(side=tk.LEFT)
        
        # Cookies文件
        cookies_frame = ttk.Frame(options_frame, style="TFrame")
        cookies_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cookies_frame, text="Cookies文件 (可选):", style="TLabel").pack(side=tk.LEFT)
        ttk.Entry(cookies_frame, textvariable=self.cookies_path_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(cookies_frame, text="浏览...", command=self.browse_cookies_file).pack(side=tk.LEFT)
        
        # 其他选项
        other_options_frame = ttk.Frame(options_frame, style="TFrame")
        other_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Checkbutton(other_options_frame, text="仅下载音频", variable=self.audio_only_var, style="TCheckbutton").pack(side=tk.LEFT, padx=5)
        
        ttk.Label(other_options_frame, text="音频分段长度(秒):", style="TLabel").pack(side=tk.LEFT, padx=5)
        ttk.Spinbox(other_options_frame, from_=60, to=3600, increment=60, textvariable=self.segment_length_var, width=5).pack(side=tk.LEFT)
        
        # 操作按钮
        buttons_frame = ttk.Frame(self.main_frame, style="TFrame")
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="开始转录", command=self.start_transcription, style="TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="取消", command=self.cancel_transcription, style="TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="打开输出文件夹", command=self.open_output_folder, style="TButton").pack(side=tk.LEFT, padx=5)
        
        # 进度条
        progress_frame = ttk.Frame(self.main_frame, style="TFrame")
        progress_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(progress_frame, text="进度:", style="TLabel").pack(side=tk.LEFT)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, length=100, mode="determinate")
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
    
    def create_log_area(self):
        """创建日志区域"""
        log_frame = ttk.LabelFrame(self.main_frame, text="处理日志", style="TFrame")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 创建日志文本区域
        self.log_text = tk.Text(log_frame, height=10, width=80, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 设置日志区域为只读
        self.log_text.config(state=tk.DISABLED)
    
    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root, relief=tk.SUNKEN, padding=(2, 2))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT)
    
    def browse_output_path(self):
        """浏览并选择输出文件夹"""
        folder_path = filedialog.askdirectory(title="选择输出文件夹")
        if folder_path:
            self.output_path_var.set(folder_path)
    
    def browse_cookies_file(self):
        """浏览并选择cookies文件"""
        file_path = filedialog.askopenfilename(title="选择Cookies文件", filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if file_path:
            self.cookies_path_var.set(file_path)
    
    def open_output_folder(self):
        """打开输出文件夹"""
        output_path = self.output_path_var.get()
        if os.path.exists(output_path):
            # 根据操作系统打开文件夹
            if sys.platform == 'win32':
                os.startfile(output_path)
            elif sys.platform == 'darwin':  # macOS
                os.system(f'open "{output_path}"')
            else:  # Linux
                os.system(f'xdg-open "{output_path}"')
        else:
            messagebox.showwarning("警告", f"输出文件夹不存在: {output_path}")
    
    def log_message(self, message):
        """向日志区域添加消息"""
        def update_log():
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)  # 自动滚动到最新内容
            self.log_text.config(state=tk.DISABLED)
        
        self.root.after(0, update_log)
    
    def update_status(self, status, progress=None):
        """更新状态栏和进度条"""
        self.status_var.set(status)
        if progress is not None:
            self.progress_var.set(progress)
    
    def start_transcription(self):
        """开始转录过程"""
        # 获取输入值
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入有效的YouTube视频URL")
            return
        
        output_path = self.output_path_var.get()
        cookies_file = self.cookies_path_var.get() if self.cookies_path_var.get() else None
        audio_only = self.audio_only_var.get()
        segment_length = self.segment_length_var.get()
        
        # 确保输出目录存在
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # 更新UI状态
        self.update_status("开始处理...", 0)
        
        # 在单独的线程中运行转录过程
        self.transcription_thread = threading.Thread(
            target=self.run_transcription, 
            args=(url, output_path, cookies_file, audio_only, segment_length)
        )
        self.transcription_thread.daemon = True
        self.transcription_thread.start()
    
    def run_transcription(self, url, output_path, cookies_file, audio_only, segment_length):
        """在后台运行转录过程"""
        try:
            # 重定向标准输出到日志
            original_stdout = sys.stdout
            original_stderr = sys.stderr
            
            class LogRedirector:
                def __init__(self, gui):
                    self.gui = gui
                    self.buffer = ""
                
                def write(self, text):
                    self.buffer += text
                    if '\n' in self.buffer:
                        lines = self.buffer.split('\n')
                        for line in lines[:-1]:
                            if line.strip():  # 忽略空行
                                self.gui.log_message(line)
                        self.buffer = lines[-1]
                
                def flush(self):
                    if self.buffer:
                        self.gui.log_message(self.buffer)
                        self.buffer = ""
            
            sys.stdout = LogRedirector(self)
            sys.stderr = LogRedirector(self)
            
            # 更新状态
            self.update_status("正在下载视频/音频...", 10)
            
            # 下载视频
            self.log_message(f"开始下载: {url}")
            file_path = download_youtube_video(url, output_path, cookies_file, audio_only)
            if not file_path:
                self.update_status("下载失败", 0)
                self.log_message("错误: 无法下载视频/音频，请检查URL是否正确和网络连接")
                return
            
            # 验证文件是否存在
            if not os.path.exists(file_path):
                self.update_status("下载文件不存在", 0)
                self.log_message(f"错误: 下载完成但文件不存在: {file_path}")
                return
                
            self.log_message(f"成功下载到: {file_path}")
            
            if audio_only:
                # 直接转录音频
                self.update_status("正在转录音频...", 50)
                self.log_message("开始转录下载的音频...")
                text_file = transcribe_audio(file_path, output_path)
            else:
                # 提取音频并转录
                self.update_status("正在提取音频...", 30)
                self.log_message("从视频中提取音频...")
                audio_file = extract_audio(file_path, output_path)
                if not audio_file:
                    self.update_status("提取音频失败", 0)
                    self.log_message("错误: 无法从视频中提取音频")
                    return
                
                # 验证音频文件是否存在
                if not os.path.exists(audio_file):
                    self.update_status("音频文件不存在", 0)
                    self.log_message(f"错误: 提取完成但音频文件不存在: {audio_file}")
                    return
                
                self.update_status("正在转录音频...", 50)
                self.log_message(f"开始转录音频: {audio_file}")
                text_file = transcribe_audio(audio_file, output_path)
            
            if not text_file:
                self.update_status("转录失败", 0)
                self.log_message("错误: 无法完成音频转录，请检查OpenAI API密钥和配置")
                return
            
            # 验证转录文件是否存在
            if not os.path.exists(text_file):
                self.update_status("转录文件不存在", 0)
                self.log_message(f"错误: 转录完成但文本文件不存在: {text_file}")
                return
            
            # 完成
            self.update_status("处理完成!", 100)
            self.log_message(f"视频URL: {url}")
            self.log_message(f"输出文件: {text_file}")
            
            # 显示成功消息
            self.root.after(0, lambda: messagebox.showinfo("完成", f"视频已成功转录!\n输出文件: {text_file}"))
            
        except Exception as e:
            error_msg = f"处理过程中出错: {str(e)}"
            self.log_message(error_msg)
            self.log_message(f"异常详情: {e.__class__.__name__}")
            self.update_status("处理失败", 0)
            self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
        
        finally:
            # 恢复标准输出
            sys.stdout = original_stdout
            sys.stderr = original_stderr
    
    def cancel_transcription(self):
        """取消转录过程"""
        # 目前没有实现取消功能，因为原始脚本没有支持
        messagebox.showinfo("信息", "取消功能暂未实现。请等待当前操作完成或重启应用。")

def main():
    root = tk.Tk()
    app = YouTubeTranscriberGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main() 