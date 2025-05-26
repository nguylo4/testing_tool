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
import math

def init_app_state(app):
    app.checklist_count = 0
    app.tree = None
    app.excel_path = None
    app.headers = []
    app.data = []
    app.project = "DAS_VW_02"
    app.working_dir = None
    app.Test_level = "30_SW_Test"
    app.Functionality = "20_SWT_CC"
    app.workspace_path = None
    app.feature_map = {
            "Cust": "Customization", "cust": "Customization", "Customization": "Customization",
            "Norm": "Normalization", "norm": "Normalization", "Normalization": "Normalization",
            "Diag": "UDSDiagnostics", "diag": "UDSDiagnostics", "UDSDiagnostics": "UDSDiagnostics",
            "DTC": "DTCandErrorHandling", "dtc": "DTCandErrorHandling",
            "ProgramSequenceMonitoring": "ProgramSequenceMonitoring", "PSM": "ProgramSequenceMonitoring",
            "SystemStateMachine": "SystemStateMachine", "stm":"SystemStateMachine" , "STM":"SystemStateMachine", "Sysstm":"SystemStateMachine", "Systemstatemachine":"SystemStateMachine", "Stm":"SystemStateMachine",
            "Sensor_Ident":"SensorIdentification", "Ident":"SensorIdentification", "Sensor_Id":"SensorIdentification", "Sensor_ID":"SensorIdentification",
            "MCUTC3x":"MCUTC3x", "MCUTC3X":"MCUTC3x", "MCUTC3x_": "MCUTC3x", "MCUTC3X_":"MCUTC3x",
            "VEI":"VEI", "AAC":"AAC", "PS":"PowerSupply",
            "VCAN":"VCAN", "Vcan":"VCAN", "Vcan_":"VCAN", "V_CAN":"VCAN", "V_CAN_":"VCAN",
            "PrivateCommunication" : "PrivateCommunication", "Private_Communication": "PrivateCommunication", "PrivateCommunication_": "PrivateCommunication",
        }



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
        "sidebar_width": app.file_sidebar.winfo_width(),
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
        

    entry.bind("<Return>", save_edit)
    refresh_table(app)
    entry.bind("<FocusOut>", lambda e: entry.destroy())
    # refresh_table(app)
def sanitize_filename(name):
    # Loại bỏ ký tự không hợp lệ cho tên file/thư mục trên Windows
    name = re.sub(r'[<>:"/\\|?*\n\r\t] ', '_', name)
    return name.strip().replace(" ", "_")


def highlight_verdict_cells(app):
    try:
        verdict_idx = app.headers.index("Test Verdict")
        for r, row in enumerate(app.data):
            verdict = str(row[verdict_idx]).strip().lower()
            if verdict == "passed":
                app.sheet.highlight_cells(row=r, column=verdict_idx, bg="#b6fcb6")
            elif verdict == "failed":
                app.sheet.highlight_cells(row=r, column=verdict_idx, bg="#ffb3b3")
            elif verdict in ("not_tested", "discarded"):
                app.sheet.highlight_cells(row=r, column=verdict_idx, bg="#fff7b2")
    except Exception:
        pass

def refresh_table(app):
    # Xóa bảng cũ nếu có
    for widget in app.main_area.winfo_children():
        widget.destroy()

    tk.Label(app.main_area, text="Working dashbroad", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

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
        filtered_row = []
        for idx in valid_indices:
            val = row[idx] if idx < len(row) and row[idx] is not None else ""
            # Chuyển nan (chuỗi hoặc float) thành khoảng trắng
            if isinstance(val, float) and math.isnan(val):
                val = ""
            elif str(val).strip().lower() == "nan":
                val = ""
            filtered_row.append(str(val).replace("_x000D_", ""))
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
        feature_idx = app.headers.index("H_Feature")
        id_idx = app.headers.index("Test cases ID")
        file_exist_idx = app.headers.index("File existed")
    except Exception:
        crid_idx = feature_idx = id_idx = file_exist_idx = None

    if crid_idx is not None and feature_idx is not None and id_idx is not None and app.working_dir:
        for row in app.data:
            crid_val = str(row[crid_idx]).strip()
            feature_val_raw = str(row[feature_idx]).strip()
            id_val = str(row[id_idx]).strip()
            # feature_map = {
            #     "Cust": "Customization", "cust": "Customization", "Customization": "Customization",
            #     "Norm": "Normalization", "norm": "Normalization", "Normalization": "Normalization",
            #     "Diag": "UDSDiagnostics", "diag": "UDSDiagnostics", "UDSDiagnostics": "UDSDiagnostics",
            #     "DTC": "DTCandErrorHandling", "dtc": "DTCandErrorHandling",
            #     "ProgramSequenceMonitoring": "ProgramSequenceMonitoring", "PSM": "ProgramSequenceMonitoring"
            # }
            feature_val = app.feature_map.get(feature_val_raw, feature_val_raw)
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
    highlight_verdict_cells(app)

    # Khi sửa sheet, cập nhật lại app.data và tô lại màu verdict
    def update_data(event=None):
        app.data = app.sheet.get_sheet_data(return_copy=True)
        highlight_verdict_cells(app)
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

def set_status(app, text, success=True):
    style_name = "StatusSuccess.TLabel" if success else "StatusError.TLabel"
    app.status_label.config(text=text, style=style_name)

def refresh_all(app):
    save_excel_table(app)
    save_workspace(app)
    refresh_table(app)
    set_status(app,"Refreshed!, Saved Excel and workspace!", success=True)




