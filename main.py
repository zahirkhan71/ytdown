import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import requests
from io import BytesIO
import yt_dlp


class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("800x600")
        self.root.resizable(True, True)

        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50", foreground="white")
        self.style.configure("TEntry", padding=6)

        # Variables
        self.video_url = tk.StringVar()
        self.selected_format = tk.StringVar()
        self.download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.available_formats = []

        self.create_widgets()

    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # URL Entry Frame
        url_frame = ttk.Frame(main_frame)
        url_frame.pack(fill=tk.X, pady=10)

        ttk.Label(url_frame, text="YouTube URL:").pack(side=tk.LEFT)
        self.url_entry = ttk.Entry(url_frame, textvariable=self.video_url, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)

        self.search_btn = ttk.Button(url_frame, text="Search", command=self.fetch_video_info)
        self.search_btn.pack(side=tk.LEFT)

        # Video Info Frame
        self.info_frame = ttk.Frame(main_frame)

        # Thumbnail Label
        self.thumbnail_label = ttk.Label(self.info_frame)
        self.thumbnail_label.pack(pady=10)

        # Title Label
        self.title_label = ttk.Label(self.info_frame, wraplength=700)
        self.title_label.pack(pady=5)

        # Format Selection
        format_frame = ttk.Frame(self.info_frame)
        format_frame.pack(pady=10)

        ttk.Label(format_frame, text="Select Quality:").pack(side=tk.LEFT)
        self.format_combo = ttk.Combobox(format_frame, textvariable=self.selected_format, state="readonly")
        self.format_combo.pack(side=tk.LEFT, padx=10)

        # Download Path Frame
        path_frame = ttk.Frame(self.info_frame)
        path_frame.pack(pady=10)

        ttk.Button(path_frame, text="Choose Folder", command=self.choose_directory).pack(side=tk.LEFT)
        self.path_label = ttk.Label(path_frame, text=self.download_path)
        self.path_label.pack(side=tk.LEFT, padx=10)

        # Download Button
        self.download_btn = ttk.Button(self.info_frame, text="Download Video", command=self.download_video)
        self.download_btn.pack(pady=10)

    def fetch_video_info(self):
        url = self.video_url.get()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return

        try:
            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)

            # Show info frame
            self.info_frame.pack(fill=tk.X, pady=20)

            # Display thumbnail
            thumbnail_url = info.get('thumbnail', '')
            response = requests.get(thumbnail_url)
            img_data = response.content
            img = Image.open(BytesIO(img_data))
            img.thumbnail((320, 180))
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_label.config(image=photo)
            self.thumbnail_label.image = photo

            # Display title
            self.title_label.config(text=info.get('title', 'No Title Found'))

            # Get all available video formats
            self.available_formats = []
            formats_set = set()

            for f in info.get('formats', []):
                if f.get('vcodec') != 'none':
                    height = f.get('height')
                    fps = f.get('fps')
                    format_note = f"{height}p{f'@{int(fps)}fps' if fps else ''}"

                    # Check if format has audio or needs merging
                    has_audio = f.get('acodec') != 'none'
                    self.available_formats.append({
                        'format_id': f['format_id'],
                        'height': height,
                        'has_audio': has_audio,
                        'format_note': format_note
                    })
                    if height:
                        formats_set.add(f"{height}p")

            # Show all unique resolutions
            self.format_combo['values'] = sorted(formats_set, key=lambda x: int(x[:-1]), reverse=True)
            if formats_set:
                self.selected_format.set(sorted(formats_set, key=lambda x: int(x[:-1]), reverse=True)[0])

        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch video info: {str(e)}")

    def choose_directory(self):
        path = filedialog.askdirectory()
        if path:
            self.download_path = path
            self.path_label.config(text=path)

    def download_video(self):
        url = self.video_url.get()
        selected_res = self.selected_format.get()
        if not url or not selected_res:
            return

        try:
            # Find the best format with selected resolution that includes audio
            ydl_opts = {
                'format': f'bestvideo[height<={selected_res[:-1]}]+bestaudio/best[height<={selected_res[:-1]}]',
                'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.download_btn.config(state=tk.DISABLED)
                ydl.download([url])
            messagebox.showinfo("Success", "Download completed successfully!")
        except yt_dlp.utils.DownloadError as e:
            if "ffmpeg is not installed" in str(e):
                messagebox.showerror("Error",
                                     "FFmpeg is required for merging audio/video streams.\n\nPlease install FFmpeg or choose a format with built-in audio.")
            else:
                messagebox.showerror("Error", f"Download failed: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Download failed: {str(e)}")
        finally:
            self.download_btn.config(state=tk.NORMAL)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            # You can add a progress bar here if needed
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
