# YouTube 视频转文本工具

一个简单的工具，可以将 YouTube 视频转换为文本报告。

## 功能

- 从 YouTube 下载视频音频
- 使用 Whisper 模型进行语音转文字
- 生成文本报告

## 依赖

- Python 3.8+
- FFmpeg
- pytube 或 yt-dlp
- openai-whisper

## 使用方法

```bash
python main.py "YouTube视频URL"
```

## 输出

程序会生成一个包含视频标题和转录内容的文本报告。
