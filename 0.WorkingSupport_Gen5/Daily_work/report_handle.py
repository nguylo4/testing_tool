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
            # Lấy chính xác phần trước /project.pj, kể cả có dấu cách
            idx = line.lower().index("/project.pj")
            subfolder = line[:idx]
            subfolders.append(subfolder)
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
    if base_subfolder:
        pj_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{project_val}/60_ST/{test_level_val}/{functionality_val}/10_{ts_env_val}/30_Reports/RC_CUST_{project_val}_SW_{release_val}.01.01/{crid_val}/{base_subfolder}/project.pj"
    else:
        pj_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{project_val}/60_ST/{test_level_val}/{functionality_val}/10_{ts_env_val}/30_Reports/RC_CUST_{project_val}_SW_{release_val}.01.01/{crid_val}/project.pj"
    cmd = f'si viewproject --project="{pj_path}" --no"'
    try:
        output = run_si_command(cmd, cwd=dest_dir)
    except RuntimeError as e:
        print(f"[WARNING] Không thể truy cập project.pj: {pj_path}\n{e}")
        return []  # Không có file nào, bỏ qua nhánh này

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

def download_report_with_si(app, info, progress_var=None, file_var=None, progress_win=None, return_log=False):
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

    downloaded_files = []
    failed_files = []
    total = len(all_html_files)
    for idx, (rel_html_path, pj_path) in enumerate(all_html_files, 1):
        html_name = os.path.basename(rel_html_path)
        html_dest = os.path.join(dest_dir, html_name)
        cmd_download = (
            f'si viewrevision --project="{pj_path}" --revision=:member "{html_name}" > "{html_dest}"'
        )
        try:
            result = subprocess.run(cmd_download, cwd=dest_dir, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                downloaded_files.append(rel_html_path)
            else:
                failed_files.append(rel_html_path)
        except Exception as e:
            failed_files.append(f"{rel_html_path} ({e})")
        if file_var:
            file_var.set(html_name)
        if progress_var:
            progress_var.set(idx * 100 / total)
        if progress_win:
            progress_win.update()
    if return_log:
        return downloaded_files, failed_files

def on_download_report(app):
    from tkinter import Toplevel, ttk, StringVar, filedialog, messagebox, scrolledtext

    # Hỏi người dùng đã connect PTC chưa
    if not messagebox.askyesno("Check connect to PTC", "Has you connect into PTC Windchill yet?\n\nChoose Yes to continue, No to open CMD for connnection."):
        subprocess.Popen("start cmd", shell=True)
        messagebox.showinfo("Hint", "Use command 'si connect' ... in CMD to connect to PTC.")
        return

    if not getattr(app, "working_dir", None):
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return

    # Lấy tất cả CR ID (dòng) trong bảng
    crid_idx = app.headers.index("CR ID")
    total_cr = len(app.data)
    progress_win = Toplevel(app)
    progress_win.title("Downloading Reports")
    progress_win.geometry("600x400")
    progress_var = tk.DoubleVar()
    file_var = StringVar()
    ttk.Label(progress_win, text="Downloading file:").pack(pady=5)
    file_label = ttk.Label(progress_win, textvariable=file_var, font=("Segoe UI", 10, "bold"))
    file_label.pack(pady=2)
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=550)
    progress_bar.pack(pady=10)
    log_text = scrolledtext.ScrolledText(progress_win, width=80, height=15, font=("Consolas", 10))
    log_text.pack(pady=5)
    log_text.insert("end", "Start download...\n")
    progress_win.update()

    download_log = []

    for idx, values in enumerate(app.data, 1):
        info = get_report_info(app, values)
        crid = info["crid_val"]
        file_var.set(f"CR: {crid}")
        progress_var.set(idx * 100 / total_cr)
        progress_win.update()

        try:
            downloaded_files, failed_files = download_report_with_si(
                app, info, progress_var=None, file_var=None, progress_win=None, return_log=True
            )
            if downloaded_files:
                log_text.insert("end", f"[OK] CR {crid}: Downloaded {len(downloaded_files)} file(s):\n")
                for f in downloaded_files:
                    log_text.insert("end", f"    {f}\n")
            if failed_files:
                log_text.insert("end", f"[FAILED] CR {crid}: Cannot download file:\n")
                for f in failed_files:
                    log_text.insert("end", f"    {f}\n")
            if not downloaded_files and not failed_files:
                log_text.insert("end", f"[FAILED] CR {crid}: Cannot found report or can not access into project.pj\n")
        except Exception as e:
            log_text.insert("end", f"[ERROR] CR {crid}: {e}\n")
        log_text.see("end")
        progress_win.update()

    log_text.insert("end", "\nCompleted download report!\n")
    ttk.Button(progress_win, text="OK", command=progress_win.destroy, bootstyle="success").pack(pady=8)
    progress_win.grab_set()
    progress_win.wait_window()

def check_report_log(app):
    from tkinter import Toplevel, ttk, StringVar, filedialog, messagebox, scrolledtext

    if not getattr(app, "working_dir", None):
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
    if not app.working_dir:
        messagebox.showwarning("Cannot save", "Please choose working directory!")
        return

    # Đảm bảo 2 cột log tồn tại
    if "Testlog_ok" not in app.headers:
        app.headers.append("Testlog_ok")
        for row in app.data:
            row.append("")
    if "Testlog_nok" not in app.headers:
        app.headers.append("Testlog_nok")
        for row in app.data:
            row.append("")

    # Lấy các index cần thiết
    try:
        id_idx = app.headers.index("Test cases ID")
        verdict_idx = app.headers.index("Test Verdict")
        release_idx = app.headers.index("Release")
        ecuid_idx = app.headers.index("ECU ID")
        crid_idx = app.headers.index("CR ID")
        testlog_ok_idx = app.headers.index("Testlog_ok")
        testlog_nok_idx = app.headers.index("Testlog_nok")
        project = app.project
    except Exception as e:
        messagebox.showerror("Error", f"Missing column: {e}")
        return

    total = len(app.data)
    # Tạo cửa sổ progress
    progress_win = Toplevel(app)
    progress_win.title("Checking Report Log")
    progress_win.geometry("600x120")
    progress_var = tk.DoubleVar()
    file_var = StringVar()
    ttk.Label(progress_win, text="Đang kiểm tra Test Case:").pack(pady=5)
    file_label = ttk.Label(progress_win, textvariable=file_var, font=("Segoe UI", 10, "bold"))
    file_label.pack(pady=2)
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=550)
    progress_bar.pack(pady=10)
    progress_win.update()

    for row_idx, values in enumerate(app.data):
        test_case_id = str(values[id_idx]).strip()
        expected_verdict = str(values[verdict_idx]).strip().lower()
        expected_release = str(values[release_idx]).strip()
        expected_ecuid = str(values[ecuid_idx]).strip()
        crid_val = str(values[crid_idx]).strip()

        # Xác định đúng dest_dir cho từng CR
        dest_dir = os.path.join(
            app.working_dir,
            f"RC_CUST_{project}_SW_{expected_release}.01.01",
            crid_val
        )

        file_var.set(f"{test_case_id} (CR: {crid_val})")
        progress_var.set((row_idx + 1) * 100 / total)
        progress_win.update()

        # Tìm tất cả file html trong dest_dir có chứa test_case_id trong tên
        html_files = []
        for root, dirs, files in os.walk(dest_dir):
            for f in files:
                if f.endswith(".html") and test_case_id in f:
                    html_files.append(os.path.join(root, f))

        # Nếu không tìm thấy report
        if not html_files:
            app.data[row_idx][testlog_ok_idx] = "report not found"
            app.data[row_idx][testlog_nok_idx] = "report not found"
            continue

        ok_list = []
        nok_list = []

        for html_file in html_files:
            with open(html_file, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # 1. Check verdict
            verdict = None
            if '<td class="NegativeResult">Test failed</td>' in content:
                verdict = "failed"
            elif '<td class="PositiveResult">Test passed</td>' in content:
                verdict = "passed"

            if verdict == expected_verdict:
                ok_list.append("Verdict")
            else:
                nok_list.append(f"Verdict in {os.path.basename(html_file)}")

            # 2. Check release
            release_pattern = re.compile(r'<td class="CellNoColor">RC_CUST_.*?_SW_(.*?)\.01\.01</td>')
            release_found = release_pattern.findall(content)
            if release_found:
                log_release = release_found[0].replace(" ", "")
                if log_release == expected_release.replace(" ", ""):
                    ok_list.append("Release")
                else:
                    nok_list.append(f"Release in {os.path.basename(html_file)}")
            else:
                nok_list.append(f"Release in {os.path.basename(html_file)}")

            # 3. Check ECU ID và Sample version
            ecu_pattern = re.compile(r'<td class="CellNoColor">(5G\d)\s.*?ECU(\d+)</td>')
            ecu_found = ecu_pattern.findall(content)
            ecu_ok = True
            sample_ok = True
            if ecu_found:
                for prefix, y in ecu_found:
                    if y not in expected_ecuid and expected_ecuid != "ALL_ECUs":
                        ecu_ok = False
                    # Sample version rule
                    if y in ("8", "9"):
                        if prefix != "5G5":
                            sample_ok = False
                    elif y in ("0", "1", "2", "3"):
                        if prefix != "5G3":
                            sample_ok = False
            else:
                ecu_ok = False
                sample_ok = False

            if ecu_ok:
                ok_list.append("ECU")
            else:
                nok_list.append(f"ECU in {os.path.basename(html_file)}")

            if sample_ok:
                ok_list.append("Sample version")
            else:
                nok_list.append(f"Sample version in {os.path.basename(html_file)}")

        # Ghi kết quả vào bảng
        app.data[row_idx][testlog_ok_idx] = "; ".join(sorted(set(ok_list)))
        app.data[row_idx][testlog_nok_idx] = "; ".join(nok_list)

    progress_win.destroy()
    refresh_table(app)