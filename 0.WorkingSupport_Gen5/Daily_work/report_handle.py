import os
import re
import subprocess
from tkinter import filedialog, messagebox
from file_ops import set_status, refresh_table, sanitize_filename
import tkinter as tk

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

def download_report_with_si(app, info, progress_var=None, file_var=None, progress_win=None):
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
        crid_val
    )
    os.makedirs(dest_dir, exist_ok=True)

    # Đệ quy lấy tất cả file html và pj_path chứa nó
    all_html_files = collect_all_html_files(
        project_val, test_level_val, functionality_val, ts_env_val, release_val, crid_val, base_subfolder="", dest_dir=dest_dir
    )

    total = len(all_html_files)
    for idx, (rel_html_path, pj_path) in enumerate(all_html_files, 1):
        html_name = os.path.basename(rel_html_path)
        if file_var:
            file_var.set(html_name)
        if progress_var:
            progress_var.set(idx * 100 / total)
        if progress_win:
            progress_win.update()
        cmd_download = (
            f'si viewrevision --project="{pj_path}" --revision=:member "{html_name}" > "{os.path.join(dest_dir, html_name)}"'
        )
        print(f"Downloading {rel_html_path} ...")
        subprocess.run(cmd_download, cwd=dest_dir, shell=True)
    print("Tải xong tất cả report!")

def on_download_report(app):
    from tkinter import Toplevel, ttk, StringVar, filedialog, messagebox

    # Hỏi người dùng đã connect PTC chưa
    if not messagebox.askyesno("Check connect to PTC", "Bạn đã connect tới PTC Windchill chưa?\nChọn Yes để tiếp tục, No để mở CMD và tự connect."):
        subprocess.Popen("start cmd", shell=True)
        messagebox.showinfo("Hướng dẫn", "Hãy dùng lệnh si connect ... trong CMD để kết nối PTC, sau đó thử lại thao tác này.")
        return

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

    # Tạo cửa sổ progress
    progress_win = Toplevel(app)
    progress_win.title("Downloading Reports")
    progress_win.geometry("400x120")
    progress_var = tk.DoubleVar()
    file_var = StringVar()
    ttk.Label(progress_win, text="Đang tải file:").pack(pady=5)
    file_label = ttk.Label(progress_win, textvariable=file_var, font=("Segoe UI", 10, "bold"))
    file_label.pack(pady=2)
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=350)
    progress_bar.pack(pady=10)
    progress_win.update()

    # Gọi hàm download có truyền progress
    download_report_with_si(app, info, progress_var, file_var, progress_win)
    progress_win.destroy()
    messagebox.showinfo("Done", "Tải xong tất cả report!")

def check_report_log(app):
    if not getattr(app, "working_dir", None):
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
    if not app.working_dir:
        messagebox.showwarning("Cannot save", "Please choose working directory!")
        return
    # Lấy dòng hiện tại
    if "Testlog_ok" not in app.headers:
        app.headers.append("Testlog_ok")
        for row in app.data:
            row.append("")
    if "Testlog_nok" not in app.headers:
        app.headers.append("Testlog_nok")
        for row in app.data:
            row.append("")
    selected_cells = app.sheet.get_selected_cells()
    if not selected_cells:
        messagebox.showwarning("Select cell", "Select a cell in the table!")
        return
    row, _ = list(selected_cells)[0]
    values = app.sheet.get_row_data(row)

    # Lấy các index cần thiết
    try:
        id_idx = app.headers.index("Test cases ID")
        verdict_idx = app.headers.index("Test Verdict")
        release_idx = app.headers.index("Release")
        ecuid_idx = app.headers.index("ECU ID")
        testlog_ok_idx = app.headers.index("Testlog_ok")
        testlog_nok_idx = app.headers.index("Testlog_nok")
        project = app.project
    except Exception as e:
        messagebox.showerror("Error", f"Missing column: {e}")
        return

    test_case_id = str(values[id_idx]).strip()
    expected_verdict = str(values[verdict_idx]).strip().lower()
    expected_release = str(values[release_idx]).strip()
    expected_ecuid = str(values[ecuid_idx]).strip()

    # Tìm tất cả file html trong working folder có chứa test_case_id trong tên
    working_dir = app.working_dir
    html_files = []
    for root, dirs, files in os.walk(working_dir):
        for f in files:
            if f.endswith(".html") and test_case_id in f:
                html_files.append(os.path.join(root, f))

    verdicts = []
    release_match = True
    ecu_match = True
    sample_version_match = True

    for html_file in html_files:
        with open(html_file, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # 1. Check verdict
        if '<td class="NegativeResult">Test failed</td>' in content:
            verdicts.append("failed")
        elif '<td class="PositiveResult">Test passed</td>' in content:
            verdicts.append("passed")

        # 2. Check release
        release_pattern = re.compile(r'<td class="CellNoColor">RC_CUST_.*?_SW_(.*?)\.01\.01</td>')
        release_found = release_pattern.findall(content)
        if release_found:
            # So sánh với release trong bảng (bỏ khoảng trắng)
            log_release = release_found[0].replace(" ", "")
            if log_release != expected_release.replace(" ", ""):
                release_match = False
        else:
            release_match = False

        # 3. Check ECU ID và Sample version
        ecu_pattern = re.compile(r'<td class="CellNoColor">(5G\d)\s.*?ECU(\d+)</td>')
        ecu_found = ecu_pattern.findall(content)
        if ecu_found:
            for prefix, y in ecu_found:
                # y là ECU ID, prefix là sample version (5G3, 5G5,...)
                if y not in expected_ecuid and expected_ecuid != "ALL_ECUs":
                    ecu_match = False
                # Sample version rule
                if y in ("8", "9"):
                    if prefix != "5G5":
                        sample_version_match = False
                elif y in ("0", "1", "2", "3"):
                    if prefix != "5G3":
                        sample_version_match = False
            print(f"ECU found: {ecu_found}")
            print(f"Expected ECU: {expected_ecuid}")
        else:
            ecu_match = False
            sample_version_match = False
        print(f"ECU found: {ecu_found}")


    # Tổng hợp kết quả
    ok_list = []
    nok_list = []

    # 1. Verdict
    final_verdict = "passed" if verdicts and all(v == "passed" for v in verdicts) else "failed"
    if final_verdict == expected_verdict:
        ok_list.append("Verdict\n")
    else:
        nok_list.append("Verdict\n")

    # 2. Release
    if release_match:
        ok_list.append("Release\n")
    else:
        nok_list.append("Release\n")

    # 3. ECU
    if ecu_match:
        ok_list.append("ECU\n")
    else:
        nok_list.append("ECU\n")

    # 4. Sample version
    if sample_version_match:
        ok_list.append("Sample version\n")
    else:
        nok_list.append("Sample version\n")

    # Ghi kết quả vào bảng
    app.data[row][testlog_ok_idx] = "; ".join(ok_list)
    app.data[row][testlog_nok_idx] = "; ".join(nok_list)
    refresh_table(app)