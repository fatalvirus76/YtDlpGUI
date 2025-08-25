# 🎥 YtDlpGUI – A graphical client for yt-dlp  

YtDlpGUI is a robust and user-friendly desktop application for **Windows, macOS, and Linux** that provides a powerful graphical interface for the popular command-line tool [yt-dlp](https://github.com/yt-dlp/yt-dlp).  

👉 Manage downloads easily with a **queue system**, view your **history**, customize **settings**, and much more.  

---

## ✨ Features  

- 📋 **Powerful queue system** – Add multiple URLs at once and manage them in a download queue.  
- ⚡ **Parallel downloads** – Download multiple files simultaneously to maximize bandwidth.  
- 🕑 **Detailed history** – View completed, failed, and canceled downloads.  
- 🖼️ **Thumbnails & playback** – Automatically shows thumbnails and lets you play files directly.  
- 🎚️ **Advanced settings** – Full control over yt-dlp arguments: choose formats, extract audio, download subtitles, etc.  
- 🎨 **Customizable themes** – Choose from Light, Dark, Synthwave, Matrix, and Dracula.  
- 📋 **Clipboard monitoring** – Detects URLs automatically and asks to add them to the queue.  
- 💾 **Save & load queue** – Export your current queue to a file and import it later.  

---

## ⚙️ Installation  

Before running the application, make sure you have **yt-dlp** and **ffmpeg** installed.  

### 1. Requirements  

- 🐍 **Python 3.10+**  
- 📥 **yt-dlp**: [Installation guide](https://github.com/yt-dlp/yt-dlp)  
- 🎬 **ffmpeg**: [Download here](https://ffmpeg.org/download.html)  
  - Required for merging audio/video and generating thumbnails.  
  - Ensure ffmpeg is in your system **PATH** or specify it in the application.  

### 2. Install the application  

```bash
# Clone the repository
git clone https://github.com/fatalvirus76/YtDlpGUI.git
cd YtDlpGUI

# Create and activate a virtual environment (highly recommended)
python3 -m venv .venv

# Activate the environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e .


🚀 Usage

Start the program from the terminal (with your virtual environment active):

python -m yt_dlp_gui_app.main


You can also create a script or shortcut for easier launching.

🛠️ First-time setup

Go to Tools > Settings.

Under the General tab, set the correct paths to your yt-dlp and ffmpeg executables.

Click OK.

Paste a URL into the top field.

Choose where to save the file.

Click Add to Queue – and you’re ready! 🎉

🤝 Contributing

Contributions are welcome!

🐛 Found a bug? Open an Issue.

💡 Have an idea? Share it.

🔧 Want to add code? Submit a Pull Request.

📜 License

This project is licensed under the MIT License.
