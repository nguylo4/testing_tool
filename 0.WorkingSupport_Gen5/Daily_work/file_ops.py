import openpyxl
import os
import datetime
import json
import webbrowser
from tkinter import filedialog, messagebox, simpledialog
import Handle_file as hf
from tkinter import ttk
import tkinter as tk
from Handle_file import save_excel_table
import tksheet
import threading
import time
import re

def init_app_state(app):
    app.checklist_count = 0
    app.tree = None
    app.excel_path = None
    app.headers = []
    app.data = []
    app.project = "DAS_VW_02"
    app.working_dir = None
    app.Test_level = "30_SW_Test"
    app.workspace_path = None



def save_workspace(app, save_as=False):
    def convert_value(val):
        if isinstance(val, datetime.datetime):
            return val.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(val, datetime.date):
            return val.strftime("%Y-%m-%d")
        return val

    serializable_data = [
        [convert_value(cell) for cell in row]
        for row in app.data
    ]
    # ...existing code...
    # Lưu width các cột nếu sheet đã được tạo
    column_widths = {}
    if hasattr(app, "sheet") and app.sheet is not None:
        for idx, col in enumerate(app.headers):
            try:
                column_widths[col] = app.sheet.column_width(idx)
            except Exception:
                column_widths[col] = 120  # mặc định

    workspace = {
        "headers": app.headers,
        "data": serializable_data,
        "sidebar_width": app.sidebar.winfo_width(),
        "main_area_width": app.main_area.winfo_width(),
        "excel_path": app.excel_path,
        "working_path": app.working_dir,
        "column_widths": column_widths,
        "project": app.project,          
        "Test_level": app.Test_level     
    }

    # Nếu đã có workspace_path và không yêu cầu lưu mới, thì lưu đè
    if hasattr(app, "workspace_path") and app.workspace_path and not save_as:
        file_path = app.workspace_path
    else:
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            set_status(app,"Canceled save workspace.", success=False)
            return
        app.workspace_path = file_path 

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(workspace, f)
    set_status(app,"Save workspace completed!", success=True)

def load_workspace(app, file_path=None):
    if not file_path:
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not file_path:
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            workspace_data = json.load(f)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Can not read workspace:\n{e}")
        return
    app.workspace_path = file_path  # Ghi nhớ đường dẫn workspace
    app.excel_path = workspace_data.get("excel_path")
    app.headers = workspace_data.get("headers", [])
    app.data = workspace_data.get("data", [])
    app.sidebar_width = workspace_data.get("sidebar_width", 200)
    app.main_area_width = workspace_data.get("main_area_width", 300)
    app.working_dir = workspace_data.get("working_path", None)
    app.column_widths = workspace_data.get("column_widths", {})
    app.project = workspace_data.get("project", getattr(app, "project", "DAS_VW_02"))
    app.Test_level = workspace_data.get("Test_level", getattr(app, "Test_level", "30_SW_Test"))
    refresh_table(app)
    set_status(app,"Workspace is opened!", success=True)
    # messagebox.showinfo("Đã mở", "Workspace đã được mở!")
    # Nếu có Entry project_var/testlevel_var thì cập nhật lại giao diện
    if hasattr(app, "project_var"):
        app.project_var.set(app.project)
    if hasattr(app, "testlevel_var"):
        app.testlevel_var.set(app.Test_level)

def open_script(app):
    selected_cells = app.sheet.get_selected_cells()
    if not selected_cells:
        messagebox.showwarning("Selecte cell", "Selecte a cell in the table!")
        return
    else:
        row, col = list(selected_cells)[0]
        values = app.sheet.get_row_data(row)
    ensure_script_file(app, values, auto_open=True)
    refresh_table(app)
    
def on_double_click(app, event):
    item = app.tree.identify_row(event.y)
    column = app.tree.identify_column(event.x)
    if not item or not column:
        return
    col_idx = int(column.replace("#", "")) - 1
    row_idx = app.tree.index(item)
    old_value = app.data[row_idx][col_idx]

    # Tạo Entry để sửa giá trị
    x, y, width, height = app.tree.bbox(item, column)
    entry = tk.Entry(app.tree)
    entry.place(x=x, y=y, width=width, height=height)
    entry.insert(0, old_value)
    entry.focus_set()

    def save_edit(event=None):
        new_value = entry.get()
        app.data[row_idx][col_idx] = new_value
        entry.destroy()
        refresh_table(app)

    entry.bind("<Return>", save_edit)
    entry.bind("<FocusOut>", lambda e: entry.destroy())
    # refresh_table(app)
def sanitize_filename(name):
    # Loại bỏ ký tự không hợp lệ cho tên file/thư mục trên Windows
    name = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    return name.strip()
def ensure_script_file(app, values, auto_open=False):
    """Đảm bảo file .can đã có ở thư mục working, nếu chưa thì tải/copy về. 
    Nếu auto_open=True thì mở file sau khi copy."""
    try:
        crid_idx = app.headers.index("CR ID")
        feature_idx = app.headers.index("Feature")
        id_idx = app.headers.index("Test cases ID")
    except ValueError:
        messagebox.showerror("Eror", "Can not found 'CR ID', 'Feature' or 'Test cases ID'!")
        return None

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

    # Chọn/tham chiếu thư mục working
    if not app.working_dir:
        app.working_dir = filedialog.askdirectory(title="Choose working directory")
        if not app.working_dir:
            messagebox.showwarning("Canot save", "Please choose working directory!")
            return None
    crid_folder = os.path.join(app.working_dir, sanitize_filename(crid_val))
    feature_folder = os.path.join(crid_folder, sanitize_filename(feature_val))
    os.makedirs(feature_folder, exist_ok=True)
    save_path = os.path.join(feature_folder, f"{sanitize_filename(id_val)}.can")
    if not id_val or not crid_val or not feature_val:
        messagebox.showwarning("Information", "Please check CR ID, Feature and Test cases ID is filled!")
        return None
    # Nếu file đã tồn tại thì trả về luôn
    if os.path.exists(save_path):
        if auto_open:
            try:
                os.startfile(save_path)
                set_status(app,f"Opened: {save_path}", success=True)
            except Exception as e:
                messagebox.showerror("Error", f"Can not open {save_path}: {e}")
                return None
        return save_path

    # Nếu chưa có file thì tải về và copy
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
        messagebox.showerror("Lỗi", f"Can not found file {id_val}.can in Download folder after 20s. Please check Feature, Project name, Test level, ID of test case or proxy!, You can see URL in web to know issue here")
        return None

    try:
        hf.copy_file_by_name(app, download_dir, feature_folder, id_val + ".can")
        set_status(app, f"Copied file into working folder successful: {save_path}", success=True)
        if auto_open:
            os.startfile(save_path)
    except Exception as e:
        messagebox.showerror("Error", f"Can not copy/open file: {e}")
        return None
    return save_path

def refresh_table(app):
    # Xóa bảng cũ nếu có
    for widget in app.main_area.winfo_children():
        widget.destroy()

    tk.Label(app.main_area, text="Working table", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

    # Tạo frame chứa sheet
    frame = tk.Frame(app.main_area)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Chỉ lọc các cột có tên (không rỗng/None)
    valid_indices = []
    valid_headers = []
    for idx, h in enumerate(app.headers):
        if h not in [None, ""]:
            valid_indices.append(idx)
            valid_headers.append(h)
    app.headers = valid_headers
    filtered_data = []
    for row in app.data:
        filtered_row = [
            str(row[idx] if idx < len(row) and row[idx] is not None else "").replace("_x000D_", "")
            for idx in valid_indices
        ]
        filtered_data.append(filtered_row)
    app.data = filtered_data

    # Thêm cột "File existed" nếu cần
    if "File existed" not in app.headers:
        app.headers.append("File existed")
        for row in app.data:
            row.append("")

    # Đánh dấu tick file tồn tại
    try:
        crid_idx = app.headers.index("CR ID")
        feature_idx = app.headers.index("Feature")
        id_idx = app.headers.index("Test cases ID")
        file_exist_idx = app.headers.index("File existed")
    except Exception:
        crid_idx = feature_idx = id_idx = file_exist_idx = None

    if crid_idx is not None and feature_idx is not None and id_idx is not None and app.working_dir:
        for row in app.data:
            crid_val = str(row[crid_idx]).strip()
            feature_val_raw = str(row[feature_idx]).strip()
            id_val = str(row[id_idx]).strip()
            feature_map = {
                "Cust": "Customization", "cust": "Customization", "Customization": "Customization",
                "Norm": "Normalization", "norm": "Normalization", "Normalization": "Normalization",
                "Diag": "UDSDiagnostics", "diag": "UDSDiagnostics", "UDSDiagnostics": "UDSDiagnostics",
                "DTC": "DTCandErrorHandling", "dtc": "DTCandErrorHandling",
                "ProgramSequenceMonitoring": "ProgramSequenceMonitoring", "PSM": "ProgramSequenceMonitoring"
            }
            feature_val = feature_map.get(feature_val_raw, feature_val_raw)
            crid_folder = os.path.join(app.working_dir, crid_val)
            feature_folder = os.path.join(crid_folder, feature_val)
            save_path = os.path.join(feature_folder, f"{id_val}.can")
            row[file_exist_idx] = "✅" if os.path.exists(save_path) else ""

    # Tạo sheet
    app.sheet = tksheet.Sheet(
        frame,
        data=app.data,
        headers=app.headers,
        show_x_scrollbar=True,
        show_y_scrollbar=True,
        width=900,
        height=500
    )
    app.sheet.enable_bindings((
        "single_select", "row_select", "column_select", "drag_select",
        "column_drag_and_drop", "row_drag_and_drop", "column_resize", "row_resize",
        "edit_cell", "arrowkeys", "right_click_popup_menu", "rc_select",
        "copy", "cut", "paste", "delete", "undo", "redo", "cell_select",
        "row_height_resize", "double_click_column_resize"
    ))
    app.sheet.pack(fill="both", expand=True)

    # --- Thêm binding cập nhật column_widths khi resize ---
    def update_column_widths(event=None):
        if not hasattr(app, "column_widths"):
            app.column_widths = {}
        for idx, col in enumerate(app.headers):
            try:
                app.column_widths[col] = app.sheet.column_width(idx)
            except Exception:
                pass

    app.sheet.extra_bindings([("column_width_resize", update_column_widths)])

    # Tô màu theo verdict
    try:
        verdict_idx = app.headers.index("Test Verdict")
        for r, row in enumerate(app.data):
            verdict = str(row[verdict_idx]).strip().lower()
            if verdict == "passed":
                app.sheet.highlight_cells(row=r, bg="#b6fcb6")
            elif verdict == "failed":
                app.sheet.highlight_cells(row=r, bg="#ffb3b3")
            elif verdict in ("not_tested", "discarded"):
                app.sheet.highlight_cells(row=r, bg="#fff7b2")
    except Exception:
        pass

    # Khi sửa sheet, cập nhật lại app.data
    def update_data(event=None):
        app.data = app.sheet.get_sheet_data(return_copy=True)
    app.sheet.extra_bindings([("end_edit_cell", update_data)])

    # Nếu muốn double click mở sửa ô, tksheet đã hỗ trợ mặc định
    # Set lại width các cột nếu có thông tin
    if hasattr(app, "column_widths") and app.column_widths:
        for idx, col in enumerate(app.headers):
            w = app.column_widths.get(col, 120)
            try:
                app.sheet.column_width(idx, w)
            except Exception:
                pass
    def update_column_widths(event=None):
        if not hasattr(app, "column_widths"):
            app.column_widths = {}
        for idx, col in enumerate(app.headers):
            try:
                app.column_widths[col] = app.sheet.column_width(idx)
            except Exception:
                pass

    app.sheet.extra_bindings([("column_width_resize", update_column_widths)])

def set_status(app, message, success=True):
        app.status_label.config(
            text=message,
            fg="#2e7d32" if success else "#c62828",
            bg="#e0e0e0"
        )
        app.status_label.after(4000, lambda: app.status_label.config(text=""))

def refresh_all(app):
    save_excel_table(app)
    save_workspace(app)
    refresh_table(app)
    set_status(app,"Đã làm mới, lưu Excel và workspace!", success=True)
