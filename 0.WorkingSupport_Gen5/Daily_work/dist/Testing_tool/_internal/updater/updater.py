import sys
import os
import time
import py7zr
import subprocess

def wait_for_process_exit(process_name, timeout=30):
    for _ in range(timeout):
        # Kiểm tra process còn chạy không
        tasks = os.popen('tasklist').read().lower()
        if process_name.lower() not in tasks:
            return True
        time.sleep(1)
    return False

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: updater.py main_app.exe update.7z app_folder")
        sys.exit(1)
    main_exe, archive_path, extract_to = sys.argv[1:4]
    print("Đợi chương trình chính thoát...")
    wait_for_process_exit(main_exe)
    print("Đang cập nhật...")
    with py7zr.SevenZipFile(archive_path, mode='r') as z:
        z.extractall(path=extract_to)
    os.remove(archive_path)
    exe_path = os.path.join(extract_to, main_exe)
    print("Đường dẫn exe sẽ chạy lại:", exe_path)
    print("File tồn tại?", os.path.exists(exe_path))
    if not os.path.exists(exe_path):
        input("Không tìm thấy file exe để chạy lại! Nhấn Enter để thoát...")
        sys.exit(1)
    print("Khởi động lại chương trình chính...")
    subprocess.Popen([exe_path])