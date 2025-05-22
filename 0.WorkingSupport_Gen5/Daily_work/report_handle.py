import os
import subprocess
from tkinter import filedialog, messagebox
from file_ops import set_status, refresh_table, sanitize_filename

def run_si_command(cmd, cwd):
    """Chạy lệnh si và trả về output (stdout) dạng string."""
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lỗi khi chạy lệnh: {cmd}\n{result.stderr}")
    return result.stdout

def parse_si_viewproject_output(output):
    """Trích xuất danh sách subfolder và file .html từ output của si viewproject."""
    subfolders = []
    html_files = []
    for line in output.splitlines():
        line = line.strip()
        if not line or line.endswith("subproject"):
            continue
        if line.endswith(".html archived 1.1"):
            fname = line.split()[0]
            if fname.lower().endswith(".html"):
                html_files.append(fname)
        elif "subproject" in line:
            subfolder = line.split()[0]
            subfolders.append(subfolder)
    return subfolders, html_files

def get_report_info(app, values):
    """Trả về dict gồm các trường cần thiết để thao tác với report file."""
    try:
        crid_idx = app.headers.index("CR ID")
        ts_env_idx = app.headers.index("TS_SW_TestEnvironment")
        release_idx = app.headers.index("Release")
        test_scope_idx = app.headers.index("Test scope")
        id_idx = app.headers.index("Test cases ID")
    except ValueError as e:
        raise Exception(f"Missing required column: {e}")

    return {
        "crid_val": sanitize_filename(values[crid_idx]),
        "project_val": app.project,
        "test_level_val": app.Test_level,
        "functionality_val": app.Functionality,
        "ts_env_val": sanitize_filename(values[ts_env_idx]),
        "release_val": sanitize_filename(values[release_idx]),
        "test_scope_val": sanitize_filename(values[test_scope_idx]),
        "id_val": sanitize_filename(values[id_idx]),
    }

def download_report_with_si(app, info):
    crid_val = info["crid_val"]
    project_val = info["project_val"]
    test_level_val = info["test_level_val"]
    functionality_val = info["functionality_val"]
    ts_env_val = info["ts_env_val"]
    release_val = info["release_val"]
    test_scope_val = info["test_scope_val"]
    id_val = info["id_val"]

    dest_dir = os.path.join(
        app.working_dir,
        f"RC_CUST_{project_val}_SW_{release_val}.01.01",
        crid_val,
        test_scope_val
    )
    os.makedirs(dest_dir, exist_ok=True)

    pj_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{project_val}/60_ST/{test_level_val}/{functionality_val}/10_{ts_env_val}/30_Reports/RC_CUST_{project_val}_SW_{release_val}.01.01/{crid_val}/project.pj"

    # 1. Lấy danh sách file/subfolder ở cấp đầu
    cmd = f'si viewproject --project="{pj_path}" --no'
    print(f"Running command: {cmd}")
    output = run_si_command(cmd, cwd=dest_dir)
    subfolders, html_files = parse_si_viewproject_output(output)

    # 2. Nếu có subfolder, lặp lại để lấy file html trong đó
    all_html_files = list(html_files)
    for sub in subfolders:
        pj_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{project_val}/60_ST/{test_level_val}/{functionality_val}/10_{ts_env_val}/30_Reports/RC_CUST_{project_val}_SW_{release_val}.01.01/{crid_val}/{sub}/project.pj"
        sub_cmd = f'si viewproject --project="{pj_path}" --no'
        sub_output = run_si_command(sub_cmd, cwd=dest_dir) 
        _, sub_html_files = parse_si_viewproject_output(sub_output)
        all_html_files.extend([os.path.join(sub, f) for f in sub_html_files])

    # 3. Download tất cả file html (không lọc theo id_val)
    for html_file in all_html_files:
        html_dest_dir = dest_dir
        if os.sep in html_file:
            html_dest_dir = os.path.join(dest_dir, os.path.dirname(html_file))
            os.makedirs(html_dest_dir, exist_ok=True)
        html_name = os.path.basename(html_file)
        cmd_download = (
            f'si viewrevision --project="{pj_path}" --revision=:member "{html_file}" > "{os.path.join(html_dest_dir, html_name)}"'
        )
        print(f"Downloading {html_file} ...")
        subprocess.run(cmd_download, cwd=html_dest_dir, shell=True)
    print("Tải xong tất cả report!")

def on_download_report(app):
    # Đảm bảo working_dir đã được chọn
    if not getattr(app, "working_dir", None):
        from tkinter import filedialog, messagebox
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return

    # Lấy dòng dữ liệu hiện tại
    selected_cells = app.sheet.get_selected_cells()
    if not selected_cells:
        messagebox.showwarning("Select cell", "Select a cell in the table!")
        return
    row, _ = list(selected_cells)[0]
    values = app.sheet.get_row_data(row)
    info = get_report_info(app, values)

    # Kiểm tra các trường trong info
    for k, v in info.items():
        if not v:
            messagebox.showerror("Error", f"Missing value for: {k}")
            return

    download_report_with_si(app, info)