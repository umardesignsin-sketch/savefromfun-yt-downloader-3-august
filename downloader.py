import subprocess
import os
import sys

def check_ffmpeg():
    """Check if ffmpeg is installed and accessible."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def download_video(url, output_path='Downloads'):
    """Download a single YouTube video."""
    try:
        print(f"\n📥 Fetching video from: {url}")
        os.makedirs(output_path, exist_ok=True)
        
        command = [
            'yt-dlp',
            '-o', os.path.join(output_path, '%(title)s.%(ext)s'),
            '--merge-output-format', 'mp4',
            url
        ]
        
        print("⏳ Downloading... (this may take a moment)")
        subprocess.run(command, check=True)
        print(f"✅ Download successful! Saved in '{output_path}'")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

def download_playlist(url, output_path='Downloads'):
    """Download all videos in a YouTube playlist."""
    try:
        print(f"\n📂 Starting playlist download: {url}")
        os.makedirs(output_path, exist_ok=True)
        
        output_template = os.path.join(
            output_path, 
            '%(playlist_title)s/%(playlist_index)s - %(title)s.%(ext)s'
        )
        
        command = [
            'yt-dlp',
            '-o', output_template,
            '--yes-playlist',
            '--merge-output-format', 'mp4',
            url
        ]
        
        print("⏳ Downloading playlist...")
        subprocess.run(command, check=True)
        print("\n✅ Playlist download complete!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Playlist download failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

def download_audio(url, output_path='Downloads'):
    """Download audio only as MP3."""
    try:
        print(f"\n🎵 Extracting audio from: {url}")
        os.makedirs(output_path, exist_ok=True)
        
        command = [
            'yt-dlp',
            '-x',  # Extract audio
            '--audio-format', 'mp3',
            '--audio-quality', '0',  # Best quality (0 = best)
            '-o', os.path.join(output_path, '%(title)s.%(ext)s'),
            url
        ]
        
        print("⏳ Extracting audio...")
        subprocess.run(command, check=True)
        print(f"✅ Audio downloaded successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Audio extraction failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

def download_custom_quality(url, quality, output_path='Downloads'):
    """Download video with custom resolution."""
    try:
        print(f"\n📥 Downloading {quality}p video from: {url}")
        os.makedirs(output_path, exist_ok=True)
        
        command = [
            'yt-dlp',
            '-f', f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            '--merge-output-format', 'mp4',
            '-o', os.path.join(output_path, '%(title)s.%(ext)s'),
            url
        ]
        
        print("⏳ Downloading...")
        subprocess.run(command, check=True)
        print(f"✅ Download successful! Saved in '{output_path}'")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Download failed: {e}")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

def main():
    """Main menu for the downloader."""
    print("=" * 50)
    print("    🎬 YOUTUBE DOWNLOADER 🎬")
    print("=" * 50)
    
    # Check if ffmpeg is installed
    if not check_ffmpeg():
        print("\n⚠️  WARNING: FFmpeg not found!")
        print("   Without FFmpeg, you'll get lower quality downloads.")
        print("   Make sure FFmpeg is installed and added to PATH.")
        print("   Continue anyway? (y/n)")
        if input().lower() != 'y':
            return
    
    while True:
        print("\n" + "-" * 50)
        print("What would you like to download?")
        print("  1. Single Video (best quality)")
        print("  2. Playlist")
        print("  3. Audio only (MP3)")
        print("  4. Custom quality (720p, 1080p, etc.)")
        print("  q. Quit")
        print("-" * 50)
        
        choice = input("Enter your choice (1-4 or q): ").strip().lower()
        
        if choice == 'q':
            print("\n👋 Goodbye!")
            break
        elif choice == '1':
            url = input("Enter YouTube URL: ").strip()
            if url:
                download_video(url)
        elif choice == '2':
            url = input("Enter Playlist URL: ").strip()
            if url:
                download_playlist(url)
        elif choice == '3':
            url = input("Enter YouTube URL: ").strip()
            if url:
                download_audio(url)
        elif choice == '4':
            url = input("Enter YouTube URL: ").strip()
            if url:
                quality = input("Enter quality (e.g., 720, 1080, 2160): ").strip()
                download_custom_quality(url, quality)
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Download cancelled. Goodbye!")
        sys.exit(0)