import sys
import os
import time
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import py7zr
import zipfile

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

def extract_7z_and_overwrite(archive_path, extract_to, set_progress=None):
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        all_files = z.getnames()
        total = len(all_files)
        for idx, name in enumerate(all_files, 1):
            z.extract(targets=[name], path=extract_to)
            if set_progress:
                percent = int(idx * 100 / total)
                set_progress(percent)
    os.remove(archive_path)

def extract_zip_and_overwrite(archive_path, extract_to, set_progress=None):
    with zipfile.ZipFile(archive_path, 'r') as z:
        all_files = z.namelist()
        total = len(all_files)
        for idx, name in enumerate(all_files, 1):
            z.extract(name, path=extract_to)
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