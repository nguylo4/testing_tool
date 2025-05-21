import requests
import py7zr
import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, messagebox
import threading

UPDATE_JSON_URL = "https://raw.githubusercontent.com/nguylo4/testing_tool/refs/heads/main/0.WorkingSupport_Gen5/Daily_work/Release_update/update_version.json"
CURRENT_VERSION = "1.2"

def get_update_info():
    resp = requests.get(UPDATE_JSON_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()

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
    # Kiểm tra file có dung lượng hợp lý không
    if os.path.getsize(dest) < 1000:  # file quá nhỏ, có thể là lỗi
        raise Exception("Downloaded file is too small, possibly not a valid 7z file.")

def extract_7z_and_overwrite(archive_path, extract_to):
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        z.extractall(path=extract_to)

def restart_app():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def update_software_gui(root):
    try:
        info = get_update_info()
        latest_version = info["version"]
        download_url = info["download_url"]
        changelog = info["change_log"]
        if latest_version > CURRENT_VERSION:
            msg = f"Có bản cập nhật mới: {latest_version}\n\nThay đổi:\n"
            for c in changelog["changes"]:
                msg += f"- [{c['type']}] {c['description']}\n"
            if not messagebox.askyesno("Software Update", msg + "\nDo you want to update?"):
                return

            # Tạo cửa sổ progress
            progress_win = tk.Toplevel(root)
            progress_win.title("Updating...")
            tk.Label(progress_win, text="Downloading update...").pack(padx=10, pady=10)
            pb = ttk.Progressbar(progress_win, orient="horizontal", length=300, mode="determinate")
            pb.pack(padx=10, pady=10)
            pb["value"] = 0

            def set_progress(val):
                pb["value"] = val
                progress_win.update_idletasks()

            def do_update():
                try:
                    filename = os.path.basename(download_url)
                    download_with_progress(download_url, filename, set_progress)
                    pb["value"] = 100
                    progress_win.update_idletasks()
                    tk.Label(progress_win, text="Extracting...").pack()
                    extract_7z_and_overwrite(filename, os.getcwd())
                    os.remove(filename)
                    progress_win.destroy()
                    messagebox.showinfo("Update", "Update successful! The application will restart.")
                    restart_app()
                except Exception as e:
                    progress_win.destroy()
                    messagebox.showerror("Update Error", str(e))

            threading.Thread(target=do_update, daemon=True).start()
        else:
            messagebox.showinfo("Information", "You are using the latest version.")
    except Exception as e:
        print(f"Update error: {e}")
        messagebox.showerror("Update Error", str(e))

# Ví dụ tích hợp vào app Tkinter
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.title("Demo Update")
#     btn = tk.Button(root, text="Kiểm tra cập nhật", command=lambda: update_software_gui(root))
#     btn.pack(padx=20, pady=20)
#     root.mainloop()