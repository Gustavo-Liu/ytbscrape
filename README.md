# YouTube视频下载与转录工具

这是一个用于下载YouTube视频并将其转录为文本的工具。该工具支持命令行和图形用户界面(GUI)两种使用方式。

## 功能特点

- 下载YouTube/B站等视频
- 提取视频中的音频
- 使用OpenAI的Whisper API转录音频为文本
- 自动格式化转录文本，使其更易阅读
- 支持命令行和图形界面两种操作方式
- 支持大型视频的分段处理

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/Gustavo-Liu/ytbscrape.git
cd ytbscrape
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 安装FFmpeg（如果尚未安装）：
   - Windows: 下载FFmpeg并添加到系统PATH
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

4. 设置OpenAI API密钥：
   - 创建一个`.env`文件
   - 添加`OPENAI_API_KEY=你的API密钥`

## 使用方法

### 图形界面(GUI)版本

运行GUI版本：
```bash
python youtube_transcriber_gui.py
```

GUI界面包含以下选项：
- **YouTube视频URL**：输入要下载和转录的视频URL
- **输出路径**：选择保存下载文件和转录文本的目录
- **Cookies文件**：（可选）用于访问需要登录的视频
- **仅下载音频**：勾选此选项仅下载音频而不是视频
- **音频分段长度**：长视频将被分割为多个片段进行处理，此选项设置每个片段的长度（秒）

操作按钮：
- **开始转录**：开始下载和转录过程
- **取消**：取消当前操作
- **打开输出文件夹**：打开存储结果的文件夹

### 命令行版本

```bash
python youtube_transcriber_ytdlp.py [视频URL] [选项]
```

选项：
- `--output`, `-o`: 输出目录路径（默认为"output"）
- `--segment-length`, `-s`: 音频分段长度（秒）（默认为600秒）
- `--cookies`, `-c`: cookies文件路径
- `--audio-only`, `-a`: 只下载音频

示例：
```bash
python youtube_transcriber_ytdlp.py https://www.youtube.com/watch?v=dQw4w9WgXcQ -o downloads -a
```

## 注意事项

1. 确保您拥有足够的磁盘空间用于下载和处理视频。
2. 转录大型视频可能需要较长时间，尤其是使用OpenAI API转录时。
3. 使用该工具时请遵守YouTube的服务条款。
4. 确保您在.env文件中正确设置了OpenAI API密钥。 