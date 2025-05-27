from tkinter import filedialog, messagebox
import os
from file_ops import set_status, refresh_table, sanitize_filename
import Handle_file as hf
import tkinter as tk
from tkinter import ttk
import datetime
import re
import subprocess

def first_line(val):
    if val is None:
        return ""
    lines = str(val).splitlines()
    if not lines:
        return ""
    return lines[0].strip()
def get_script_info(app, values):
    """Trả về dict gồm các trường cần thiết để thao tác với script file."""
    crid_idx = app.headers.index("CR ID")
    feature_idx = app.headers.index("H_Feature")
    id_idx = app.headers.index("Test cases ID")
    crid_val = str(values[crid_idx]).strip()
    feature_val_raw = first_line(str(values[feature_idx]).strip())
    id_val = str(values[id_idx]).strip()
    # feature_map = {
    #     "Cust": "Customization", "cust": "Customization", "Customization": "Customization",
    #     "Norm": "Normalization", "norm": "Normalization", "Normalization": "Normalization",
    #     "Diag": "UDSDiagnostics", "diag": "UDSDiagnostics", "UDSDiagnostics": "UDSDiagnostics",
    #     "DTC": "DTCandErrorHandling", "dtc": "DTCandErrorHandling",
    #     "ProgramSequenceMonitoring": "ProgramSequenceMonitoring", "PSM": "ProgramSequenceMonitoring"

    # }
    feature_val = app.feature_map.get(feature_val_raw, feature_val_raw)
    crid_folder = os.path.join(app.working_dir, sanitize_filename(crid_val))
    feature_folder = os.path.join(crid_folder, sanitize_filename(feature_val))
    save_path = os.path.join(feature_folder, f"{sanitize_filename(id_val)}.can")
    return {
        "crid_val": crid_val,
        "feature_val": feature_val,
        "id_val": id_val,
        "feature_folder": feature_folder,
        "save_path": save_path
    }


def ensure_script_file(app, values, auto_open=False):
    """Đảm bảo file .can đã có ở thư mục working, nếu chưa thì tải/copy về. 
    Nếu auto_open=True thì mở file sau khi copy."""
    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return
    info = get_script_info(app, values)
    crid_val = info["crid_val"]
    feature_val = info["feature_val"]
    id_val = info["id_val"]
    feature_folder = info["feature_folder"]
    save_path = info["save_path"]

    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return None

    os.makedirs(feature_folder, exist_ok=True)

    # Nếu file đã tồn tại thì trả về luôn (và mở nếu auto_open)
    if os.path.exists(save_path):
        if auto_open:
            try:
                os.startfile(save_path)
                set_status(app, f"Opened: {save_path}", success=True)
            except Exception as e:
                messagebox.showerror("Error", f"Can not open {save_path}: {e}")
                return None
        return save_path

    # Nếu chưa có file thì tải về và copy
    ok = download_script(app)
    if not ok:
        return None

    if auto_open:
        try:
            os.startfile(save_path)
            set_status(app, f"Opened: {save_path}", success=True)
        except Exception as e:
            messagebox.showerror("Error", f"Can not open {save_path}: {e}")
            return None
    return save_path

def open_script(app):
    if not hasattr(app, "sheet") or app.sheet is None:
        messagebox.showwarning("No table", "No table loaded!")
        return

    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot open", "Please choose working directory!")
            return

    selected_cells = app.sheet.get_selected_cells()
    if not selected_cells:
        messagebox.showwarning("Select cell", "Select a cell in the table!")
        return
    row, _ = list(selected_cells)[0]
    values = app.sheet.get_row_data(row)
    info = get_script_info(app, values)
    save_path = info["save_path"]

    if os.path.exists(save_path):
        try:
            os.startfile(save_path)
            set_status(app, f"Opened: {save_path}", success=True)
        except Exception as e:
            messagebox.showerror("Error", f"Can not open {save_path}: {e}")
        return

    # Nếu chưa có script, hỏi có muốn download không
    res = messagebox.askyesno("Script not found", "Script does not exist. Do you want to download script?")
    if res:
        download_script(app)
    else:
        set_status(app, "Canceled open script.", success=False)
    try:
        os.startfile(save_path)
        set_status(app, f"Opened: {save_path}", success=True)
    except Exception as e:
        messagebox.showerror("Error", f"Can not open {save_path}: {e}")
        return


def clean_multiline_text(text):
    """Giữ lại tối đa 1 dòng trống liên tiếp, loại bỏ các dòng trống dư thừa."""
    # Loại bỏ khoảng trắng đầu/cuối mỗi dòng
    lines = [line.rstrip() for line in text.splitlines()]
    text = "\n".join(lines)
    # Thay thế 3 hoặc nhiều lần xuống dòng liên tiếp thành 2 lần xuống dòng
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def create_new_script(app):
    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return
    if not hasattr(app, "sheet") or app.sheet is None:
        messagebox.showwarning("No table", "No table loaded!")
        return

    selected = app.sheet.get_selected_cells()
    if not selected:
        messagebox.showwarning("Chọn dòng", "Hãy chọn một dòng trong bảng!")
        return
    row_idx, _ = list(selected)[0]
    values = app.sheet.get_row_data(row_idx)

    try:
        content_idx = app.headers.index("Content Requirement")
        desc_idx = app.headers.index("TS_TestDescription")
        goal_idx = app.headers.index("TS_TestGoal")
        release_idx = app.headers.index("Release")  # Thêm dòng này
    except ValueError:
        messagebox.showerror("Error", "Can not find required columns!")
        return None

    info = get_script_info(app, values)
    crid_val = info["crid_val"]
    feature_val = info["feature_val"]
    id_val = info["id_val"]
    feature_folder = info["feature_folder"]
    save_path = info["save_path"]

    content_val = str(values[content_idx]).strip() if content_idx is not None else ""
    desc_val = str(values[desc_idx]).strip() if desc_idx is not None else ""
    goal_val = str(values[goal_idx]).strip() if goal_idx is not None else ""
    release_val = str(values[release_idx]).strip() if release_idx is not None else ""  # Thêm dòng này

    # Làm sạch nội dung để tránh xuống dòng quá nhiều
    content_val = clean_multiline_text(content_val)
    desc_val = clean_multiline_text(desc_val)

    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return None

    os.makedirs(feature_folder, exist_ok=True)

    # Nếu file đã tồn tại, hỏi người dùng có muốn ghi đè không
    if os.path.exists(save_path):
        res = messagebox.askyesno("Script existed", f"Script {id_val}.can already exists. Do you want to overwrite?")
        if not res:
            set_status(app, "Canceled create script.", success=False)
            return

    # Đọc template
    template_path = os.path.join(os.path.dirname(__file__), "template", "template.can")
    if not os.path.exists(template_path):
        messagebox.showerror("Error", f"Cannot found template file: {template_path}")
        return None
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Thay thế các trường trong template
    template = template.replace("<testgoal>", goal_val)
    template = template.replace("<SW_release>", release_val)  # Sửa dòng này
    template = template.replace("<Tester>", os.getlogin())
    template = template.replace("<ImplDate>", datetime.datetime.now().strftime("%Y-%m-%d"))
    template = template.replace("<Requirement Content>", content_val)
    template = template.replace("<TS_TestDescription>", desc_val)
    template = template.replace("<Test cases ID>", id_val)
    template = template.replace("<Feature>", feature_val)

    try:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(template)
        set_status(app, f"Created new script file: {save_path}", success=True)
        os.startfile(save_path)
    except Exception as e:
        messagebox.showerror("Error", f"Can not create/open file: {e}")
        return None

    return save_path

def download_script(app, info, progress_var=None, file_var=None, progress_win=None, return_log=False):
    import subprocess
    import time
    import os

    feature_val = info["feature_val"]
    id_val = info["id_val"]
    save_path = info["save_path"]
    feature_folder = info["feature_folder"]

    pj_path = (
        f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/{app.project}/60_ST/{app.Test_level}/10_Debugger_Test/20_Scripts/Test_Cases/"
        f"{feature_val}/project.pj"
    )

    os.makedirs(feature_folder, exist_ok=True)

    # Nếu file đã tồn tại, hỏi người dùng có muốn ghi đè không
    if os.path.exists(save_path):
        res = messagebox.askyesno("Script existed", "Script already exists. Do you want to download and overwrite?")
        if not res:
            set_status(app, "Canceled download script.", success=False)
            return False

    # Tải file bằng si viewrevision
    cmd_download = (
        f'si viewrevision --project="{pj_path}" --revision=:member "{id_val}.can" > "{save_path}"'
    )
    try:
        result = subprocess.run(cmd_download, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            set_status(app, f"Downloaded script: {save_path}", success=True)
            if return_log:
                return [save_path], []
            return True
        else:
            messagebox.showerror("Error", f"Cannot download script:\n{result.stderr}")
            if return_log:
                return [], [save_path]
            return False
    except Exception as e:
        messagebox.showerror("Error", f"Cannot download script: {e}")
        if return_log:
            return [], [f"{save_path} ({e})"]
        return False

def on_download_script(app):
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

    # Lấy index các trường cần thiết
    try:
        crid_idx = app.headers.index("CR ID")
        id_idx = app.headers.index("Test cases ID")
    except Exception as e:
        messagebox.showerror("Error", f"Missing column: {e}")
        return

    total_cr = len(app.data)
    progress_win = Toplevel(app)
    progress_win.title("Downloading Scripts")
    progress_win.geometry("600x400")
    progress_var = tk.DoubleVar()
    file_var = StringVar()
    ttk.Label(progress_win, text="Downloading script:").pack(pady=5)
    file_label = ttk.Label(progress_win, textvariable=file_var, font=("Segoe UI", 10, "bold"))
    file_label.pack(pady=2)
    progress_bar = ttk.Progressbar(progress_win, variable=progress_var, maximum=100, length=550)
    progress_bar.pack(pady=10)
    log_text = scrolledtext.ScrolledText(progress_win, width=80, height=15, font=("Consolas", 10))
    log_text.pack(pady=5)
    log_text.insert("end", "Start download scripts...\n")
    progress_win.update()

    for idx, values in enumerate(app.data, 1):
        info = get_script_info(app, values)
        crid = values[crid_idx]
        script_id = values[id_idx]
        file_var.set(f"CR: {crid} - Script: {script_id}")
        progress_var.set(idx * 100 / total_cr)
        progress_win.update()

        try:
            downloaded_files, failed_files = download_script(
                app, info, progress_var=None, file_var=None, progress_win=None, return_log=True
            )
            if downloaded_files:
                log_text.insert("end", f"[OK] CR {crid}: Downloaded script(s):\n")
                for f in downloaded_files:
                    log_text.insert("end", f"    {f}\n")
            if failed_files:
                log_text.insert("end", f"[FAILED] CR {crid}: Cannot download script(s):\n")
                for f in failed_files:
                    log_text.insert("end", f"    {f}\n")
            if not downloaded_files and not failed_files:
                log_text.insert("end", f"[FAILED] CR {crid}: Cannot find script or cannot access project.pj\n")
        except Exception as e:
            log_text.insert("end", f"[ERROR] CR {crid}: {e}\n")
        log_text.see("end")
        progress_win.update()

    log_text.insert("end", "\nCompleted download scripts!\n")
    ttk.Button(progress_win, text="OK", command=progress_win.destroy, bootstyle="success").pack(pady=8)
    progress_win.grab_set()
    progress_win.wait_window()
