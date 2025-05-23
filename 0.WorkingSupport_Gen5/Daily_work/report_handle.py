import os
import subprocess
from tkinter import filedialog, messagebox
from file_ops import set_status, refresh_table, sanitize_filename

def run_si_command(cmd, cwd):
    """Chạy lệnh si và trả về output (stdout) dạng string."""
    result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Lỗi khi chạy lệnh: {cmd}\n{result.stderr}")
    print(f"Đã chạy lệnh: {cmd}")
    print(f"Output: {result.stdout}")
    return result.stdout

def parse_si_viewproject_output(output):
    """Trích xuất danh sách subfolder và file .html từ output của si viewproject."""
    subfolders = []
    html_files = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        # Tìm subfolder: dòng có dạng "Regression/project.pj subproject"
        if line.endswith("subproject") and "/project.pj" in line:
            subname = line.split()[0]
            # Lấy phần trước /project.pj
            if subname.lower().endswith("/project.pj"):
                subfolders.append(subname[:-len("/project.pj")])
            else:
                subfolders.append(subname)
            continue
        # Tìm file html
        if ".html" in line and "archived" in line:
            fname = line.split()[0]
            if fname.lower().endswith(".html"):
                html_files.append(fname)
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

def collect_all_html_files(project_val, test_level_val, functionality_val, ts_env_val, release_val, crid_val, base_subfolder, dest_dir):
    """
    Đệ quy lấy tất cả file .html và đường dẫn subfolder (nếu có) trong crid_val.
    Trả về list các tuple (relative_html_path, pj_path chứa nó).
    """
    if base_subfolder:
        pj_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{project_val}/60_ST/{test_level_val}/{functionality_val}/10_{ts_env_val}/30_Reports/RC_CUST_{project_val}_SW_{release_val}.01.01/{crid_val}/{base_subfolder}/project.pj"
    else:
        pj_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{project_val}/60_ST/{test_level_val}/{functionality_val}/10_{ts_env_val}/30_Reports/RC_CUST_{project_val}_SW_{release_val}.01.01/{crid_val}/project.pj"
    cmd = f'si viewproject --project="{pj_path}" --no'
    output = run_si_command(cmd, cwd=dest_dir)
    subfolders, html_files = parse_si_viewproject_output(output)
    print (f"Đã tìm thấy {subfolders} subfolder(s) và {html_files} file(s) .html trong {pj_path}")
    html_list = []
    for f in html_files:
        rel_path = os.path.join(base_subfolder, f) if base_subfolder else f
        html_list.append((rel_path, pj_path))

    # Đệ quy cho từng subfolder
    for sub in subfolders:
        # sub có dạng "Cust/project.pj" hoặc "Cust/Regression/project.pj"
        if sub.lower().endswith("/project.pj"):
            sub_name = sub[:-len("/project.pj")]
        else:
            sub_name = sub
        # next_base là đường dẫn tương đối từ gốc crid_val
        next_base = os.path.join(base_subfolder, sub_name) if base_subfolder else sub_name
        html_list.extend(collect_all_html_files(
            project_val, test_level_val, functionality_val, ts_env_val, release_val, crid_val, next_base, dest_dir
        ))
        print(f"Đang duyệt subfolder: {sub_name}")
    print(html_list)
    return html_list

def download_report_with_si(app, info):
    crid_val = info["crid_val"]
    project_val = info["project_val"]
    test_level_val = info["test_level_val"]
    functionality_val = info["functionality_val"]
    ts_env_val = info["ts_env_val"]
    release_val = info["release_val"]
    test_scope_val = info["test_scope_val"]

    dest_dir = os.path.join(
        app.working_dir,
        f"RC_CUST_{project_val}_SW_{release_val}.01.01",
        crid_val,
        test_scope_val
    )
    os.makedirs(dest_dir, exist_ok=True)

    # Đệ quy lấy tất cả file html và pj_path chứa nó
    all_html_files = collect_all_html_files(
        project_val, test_level_val, functionality_val, ts_env_val, release_val, crid_val, base_subfolder="", dest_dir=dest_dir
    )

    for rel_html_path, pj_path in all_html_files:
        html_dest_dir = os.path.join(dest_dir, os.path.dirname(rel_html_path)) if os.sep in rel_html_path else dest_dir
        os.makedirs(html_dest_dir, exist_ok=True)
        html_name = os.path.basename(rel_html_path)
        cmd_download = (
            f'si viewrevision --project="{pj_path}" --revision=:member "{html_name}" > "{os.path.join(html_dest_dir, html_name)}"'
        )
        print(f"Downloading {rel_html_path} ...")
        subprocess.run(cmd_download, cwd=html_dest_dir, shell=True)
    print("Tải xong tất cả report!")

def on_download_report(app):
    # Hỏi người dùng đã connect PTC chưa
    if messagebox.askyesno("Check connect to PTC", "Has you connect to PTC Windchill yet?\n Yes is continue to download, No is open CMD for you to connect PTC"):
        pass  # Tiếp tục thực hiện download
    else:
        subprocess.Popen("start cmd", shell=True)
        messagebox.showinfo("Action", "Use command 'si connect' ... in CMD for connect into PTC, when you finish, please click OK to continue!")
        pass

    if not getattr(app, "working_dir", None):
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