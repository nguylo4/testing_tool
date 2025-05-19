from tkinter import filedialog, messagebox
import os
import time
import webbrowser
import shutil
from file_ops import set_status, refresh_table, sanitize_filename
import Handle_file as hf
import tkinter as tk
from tkinter import ttk
import datetime

def get_script_info(app, values):
    """Trả về dict gồm các trường cần thiết để thao tác với script file."""
    crid_idx = app.headers.index("CR ID")
    feature_idx = app.headers.index("H_Feature")
    id_idx = app.headers.index("Test cases ID")
    crid_val = str(values[crid_idx]).strip()
    feature_val_raw = str(values[feature_idx]).strip()
    id_val = str(values[id_idx]).strip()
    feature_map = {
        "Cust": "Customization", "cust": "Customization", "Customization": "Customization",
        "Norm": "Normalization", "norm": "Normalization", "Normalization": "Normalization",
        "Diag": "UDSDiagnostics", "diag": "UDSDiagnostics", "UDSDiagnostics": "UDSDiagnostics",
        "DTC": "DTCandErrorHandling", "dtc": "DTCandErrorHandling",
        "ProgramSequenceMonitoring": "ProgramSequenceMonitoring", "PSM": "ProgramSequenceMonitoring"
    }
    feature_val = feature_map.get(feature_val_raw, feature_val_raw)
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

def download_script(app):
    import time
    import webbrowser
    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
            return

    selected_cells = app.sheet.get_selected_cells()
    if not selected_cells:
        messagebox.showwarning("Select cell", "Select a cell in the table!")
        return
    row, _ = list(selected_cells)[0]
    values = app.sheet.get_row_data(row)
    info = get_script_info(app, values)
    feature_val = info["feature_val"]
    id_val = info["id_val"]
    save_path = info["save_path"]

    # Nếu file đã tồn tại, hỏi người dùng có muốn ghi đè không
    if os.path.exists(save_path):
        res = messagebox.askyesno("Script existed", "Script already exists. Do you want to download and overwrite?")
        if not res:
            set_status(app, "Canceled download script.", success=False)
            return

    # Tạo URL download
    url = (
        f"http://mks1.dc.hella.com:7001/si/viewrevision?"
        f"projectName=e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{app.project}/60_ST/{app.Test_level}/20_SWT_CC/10_Debugger_Test/20_Scripts/Test_Cases/"
        f"{feature_val}/project.pj&selection={id_val}.can&revision=:member"
    )
    webbrowser.open(url)
    set_status(app, "Downloading, Please wait a file is arrived in Download...", success=True)
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    src_file = os.path.join(download_dir, id_val + ".can")

    # --- Hiện progress bar ở footer ---
    app.progress_var.set(0)
    app.progress_bar.lift()
    app.progress_bar.update()
    app.progress_bar.place(relx=0.5, rely=1.0, anchor="s", y=-5)
    app.progress_bar["maximum"] = 20

    found = False
    for i in range(20):
        app.progress_var.set(i + 1)
        app.progress_bar.update()
        app.update()
        time.sleep(1)
        if os.path.exists(src_file):
            found = True
            break

    app.progress_bar.lower()  # Ẩn progress bar sau khi xong

    if not found:
        messagebox.showerror(
            "Lỗi",
            f"Can not found file {id_val}.can in Download folder after 20s. Please check Feature, Project name, Test level, ID of test case or proxy!, You can see URL in web to know issue here"
        )
        return False

    try:
        hf.copy_file_by_name(app, download_dir, os.path.dirname(save_path), id_val + ".can")
        set_status(app, f"Copied file into working folder successful: {save_path}", success=True)
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Can not copy/open file: {e}")
        return False

def create_new_script(app):
    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Cannot save", "Please choose working directory!")
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
    template = template.replace("<SW_release>", getattr(app, "Test_level", ""))
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