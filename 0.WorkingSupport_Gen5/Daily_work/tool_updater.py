import requests
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

UPDATE_JSON_URL = "https://raw.githubusercontent.com/nguylo4/testing_tool/refs/heads/main/0.WorkingSupport_Gen5/Daily_work/Release_update/update_version.json"
CURRENT_VERSION = "1.3"

def get_update_info():
    resp = requests.get(UPDATE_JSON_URL, timeout=5)
    resp.raise_for_status()
    return resp.json()

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
            msg = f"New update version: {latest_version}\n\nThe change:\n"
            for c in changelog["changes"]:
                msg += f"- [{c['type']}] {c['description']}\n"
            if not messagebox.askyesno("Software Update", msg + "\nDo you want to update?"):
                return

            # Gọi updater.py, truyền main_exe, download_url, extract_to
            updater_path = os.path.join(os.path.dirname(sys.argv[0]), "updater.exe")
            main_exe = os.path.basename(sys.argv[0])
            subprocess.Popen([updater_path, main_exe, download_url, os.getcwd()])
            root.destroy()  # hoặc os._exit(0)
        else:
            messagebox.showinfo("Information", "You are using the latest version.")
    except Exception as e:
        print(f"Update error: {e}")
        messagebox.showerror("Update Error", str(e))

# Ví dụ tích hợp vào app Tkinter
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Demo Update")
    btn = tk.Button(root, text="Check for update", command=lambda: update_software_gui(root))
    btn.pack(padx=20, pady=20)
    root.mainloop()