import requests

CURRENT_VERSION = "1.2"

def check_update():
    try:
        # Thay URL này bằng link thật của bạn (ví dụ: GitHub raw, server, v.v.)
        url = "https://gist.githubusercontent.com/nguylo4/f7ad8d75fcde6554f55c77a13ff7d361/raw/656296d358728c27d5d726783724d3808a0419ac/version.json"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            latest = data.get("version", "")
            if latest > CURRENT_VERSION:
                return f"Có bản cập nhật mới: {latest}"
            else:
                return "Bạn đang dùng bản mới nhất."
        else:
            return "Không thể kiểm tra cập nhật."
    except Exception as e:
        print(e)
        return f"Lỗi kiểm tra cập nhật: {e}"

def download_update(url, filename):
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return "Tải file thành công!"
    except Exception as e:
        return f"Lỗi tải file: {e}"

# Ví dụ sử dụng:
url = "https://github.com/nguylo4/testing_tool/releases/download/v1.2/updatefile.7z"
filename = "updatefile.7z"
print(download_update(url, filename))
