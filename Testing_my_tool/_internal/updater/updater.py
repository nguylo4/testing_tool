import sys
import os
import time
import py7zr
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

def wait_for_process_exit(process_name, timeout=30):
    for _ in range(timeout):
        # Kiểm tra process còn chạy không
        tasks = os.popen('tasklist').read().lower()
        if process_name.lower() not in tasks:
            return True
        time.sleep(1)
    return False

def extract_with_progress(archive_path, extract_to, set_progress):
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        all_files = z.getnames()
        total = len(all_files)
        for idx, name in enumerate(all_files, 1):
            z.extract(targets=[name], path=extract_to)
            percent = int(idx * 100 / total)
            set_progress(percent)
    os.remove(archive_path)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: updater.py main_app.exe update.7z app_folder")
        sys.exit(1)
    main_exe, archive_path, extract_to = sys.argv[1:4]
    print("Đợi chương trình chính thoát...")
    wait_for_process_exit(main_exe)
    print("Đang cập nhật...")

    # GUI progress
    root = tk.Tk()
    root.title("Updating...")
    root.attributes('-topmost', True)
    label = tk.Label(root, text="Extracting update...")
    label.pack(padx=10, pady=10)
    pb = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
    pb.pack(padx=10, pady=10)
    pb["value"] = 0

    def set_progress(val):
        pb["value"] = val
        root.update_idletasks()

    def do_extract():
        try:
            label.config(text="Extracting update...")
            extract_with_progress(archive_path, extract_to, set_progress)
            pb["value"] = 100
            root.update_idletasks()
            label.config(text="Update completed! Restarting...")
            exe_path = os.path.join(extract_to, main_exe)
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path])
                print(f"Restarting {exe_path}...")
            else:
                messagebox.showerror("Error", f"Cannot find {exe_path} to restart!")
            root.after(1500, root.destroy)
        except Exception as e:
            print(e)
            messagebox.showerror("Update Error", str(e))
            root.destroy()

    root.after(100, do_extract)
    root.mainloop()