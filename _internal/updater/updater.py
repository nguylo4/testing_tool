import sys
import os
import time
import py7zr
import subprocess

def main(target_exe, archive_path, extract_to):
    # Đợi chương trình chính thoát hoàn toàn
    for _ in range(30):
        if not any(target_exe.lower() in p.lower() for p in os.popen('tasklist').read().splitlines()):
            break
        time.sleep(1)
    else:
        print("Timeout waiting for main app to exit.")
        sys.exit(1)
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        z.extractall(path=extract_to)
    os.remove(archive_path)
    subprocess.Popen([sys.executable, os.path.join(extract_to, target_exe)])

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: updater.py main_app.exe update.7z app_folder")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])