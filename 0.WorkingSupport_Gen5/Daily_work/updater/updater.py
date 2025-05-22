import sys
import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import zipfile
import shutil
import glob

def download_with_progress(url, dest, progress_callback):
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = int(downloaded * 100 / total) if total else 0
                    progress_callback(percent)
    progress_callback(100)
    if os.path.getsize(dest) < 1000:
        raise Exception("Downloaded file is too small, possibly not a valid archive.")

def extract_zip_and_overwrite(archive_path, extract_to, set_progress=None):
    import tempfile
    with zipfile.ZipFile(archive_path, 'r') as z:
        all_files = z.namelist()
        total = len(all_files)
        for idx, name in enumerate(all_files, 1):
            # Giải nén ra thư mục tạm trước
            with tempfile.TemporaryDirectory() as tmpdir:
                z.extract(name, path=tmpdir)
                src_file = os.path.join(tmpdir, name)
                dest_file = os.path.join(extract_to, name)
                dest_dir = os.path.dirname(dest_file)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                safe_replace(src_file, dest_file)
            if set_progress:
                percent = int(idx * 100 / total)
                set_progress(percent)
    os.remove(archive_path)

def wait_for_process_exit(process_name, timeout=30):
    for _ in range(timeout):
        tasks = os.popen('tasklist').read().lower()
        if process_name.lower() not in tasks:
            return True
        time.sleep(1)
    return False

def safe_replace(src_file, dest_file):
    try:
        if os.path.exists(dest_file):
            try:
                # Đổi tên file cũ nếu đang bị khóa
                old_file = dest_file + ".old"
                os.rename(dest_file, old_file)
                print(f"Renamed locked file: {dest_file} → {old_file}")
            except PermissionError:
                print(f"File is in use and cannot be renamed: {dest_file}")
                return False

        shutil.copy2(src_file, dest_file)
        print(f"Updated: {dest_file}")
        return True
    except Exception as e:
        print(f"Failed to update {dest_file}: {e}")
        return False

def remove_old_files(folder):
    for root_dir, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.old'):
                try:
                    os.remove(os.path.join(root_dir, file))
                except Exception as e:
                    print(f"Could not remove {file}: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: updater.py main_app.exe download_url extract_to")
        sys.exit(1)
    main_exe, download_url, extract_to = sys.argv[1:4]
    wait_for_process_exit(main_exe)

    root = tk.Tk()
    root.title("Updating...")
    root.attributes('-topmost', True)
    label = tk.Label(root, text="Downloading update...")
    label.pack(padx=10, pady=10)
    pb = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    pb.pack(padx=10, pady=10)
    pb["value"] = 0

    def set_progress(val):
        pb["value"] = val
        root.update_idletasks()

    def do_update():
        try:
            # Download
            label.config(text="Downloading update...")
            download_with_progress(download_url, "update.zip", set_progress)
            # Extract
            label.config(text="Extracting update...")
            extract_zip_and_overwrite("update.zip", extract_to, set_progress)
            pb["value"] = 100
            root.update_idletasks()
            label.config(text="Update completed! Restarting...")

            # Xóa file .old
            remove_old_files(extract_to)

            exe_path = os.path.join(extract_to, main_exe)
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path])
            else:
                messagebox.showerror("Error", f"Cannot find {exe_path} to restart!")
            root.after(1500, root.destroy)
        except Exception as e:
            messagebox.showerror("Update Error", str(e))
            root.destroy()

    root.after(100, do_update)
    root.mainloop()