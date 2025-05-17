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
    # Lưu width các cột nếu tree đã được tạo
    column_widths = {}
    if hasattr(app, "tree") and app.tree is not None:
        for col in app.headers:
            try:
                column_widths[col] = app.tree.column(col)["width"]
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
    }

    # Nếu đã có workspace_path và không yêu cầu lưu mới, thì lưu đè
    if hasattr(app, "workspace_path") and app.workspace_path and not save_as:
        file_path = app.workspace_path
    else:
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if not file_path:
            set_status(app,"Hủy lưu workspace.", success=False)
            return
        app.workspace_path = file_path 

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(workspace, f)
    set_status(app,"Đã lưu workspace thành công!", success=True)

def load_workspace(app):
    file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
    if not file_path:
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            workspace_data = json.load(f)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc workspace:\n{e}")
        return
    app.workspace_path = file_path  # Ghi nhớ đường dẫn workspace
    app.excel_path = workspace_data.get("excel_path")
    app.headers = workspace_data.get("headers", [])
    app.data = workspace_data.get("data", [])
    app.sidebar_width = workspace_data.get("sidebar_width", 200)
    app.main_area_width = workspace_data.get("main_area_width", 300)
    app.working_dir = workspace_data.get("working_path", None)
    app.column_widths = workspace_data.get("column_widths", {})
    refresh_table(app)
    set_status(app,"Workspace đã được mở!", success=True)
    # messagebox.showinfo("Đã mở", "Workspace đã được mở!")

def open_script(app):
    selected = app.tree.focus()
    if not selected:
        messagebox.showwarning("Chọn dòng", "Hãy chọn một dòng trong bảng!")
        return
    values = app.tree.item(selected, "values")
    ensure_script_file(app,values, auto_open=True)
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

def ensure_script_file(app, values, auto_open=False):
    """Đảm bảo file .can đã có ở thư mục working, nếu chưa thì tải/copy về. 
    Nếu auto_open=True thì mở file sau khi copy."""
    try:
        crid_idx = app.headers.index("CR Related")
        feature_idx = app.headers.index("Feature")
        id_idx = app.headers.index("Test cases ID")
    except ValueError:
        messagebox.showerror("Lỗi", "Không tìm thấy cột 'CR ID', 'Feature' hoặc 'Test cases ID'!")
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
        app.working_dir = filedialog.askdirectory(title="Chọn thư mục working để lưu script")
        if not app.working_dir:
            messagebox.showwarning("Chưa chọn thư mục", "Hãy chọn thư mục để lưu script!")
            return None
    crid_folder = os.path.join(app.working_dir, crid_val)
    feature_folder = os.path.join(crid_folder, feature_val)
    os.makedirs(feature_folder, exist_ok=True)
    save_path = os.path.join(feature_folder, f"{id_val}.can")

    # Nếu file đã tồn tại thì trả về luôn
    if os.path.exists(save_path):
        if auto_open:
            try:
                os.startfile(save_path)
                set_status(app,f"Đã mở file: {save_path}", success=True)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở file {save_path}: {e}")
                return None
        return save_path

    # Nếu chưa có file thì tải về và copy
    url = (
        f"http://mks1.dc.hella.com:7001/si/viewrevision?"
        f"projectName=e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{app.project}/60_ST/{app.Test_level}/20_SWT_CC/10_Debugger_Test/20_Scripts/Test_Cases/"
        f"{feature_val}/project.pj&selection={id_val}.can&revision=:member"
    )
    webbrowser.open(url)
    set_status(app,"Đang tải file, vui lòng tải file về thư mục Download...", success=True)
    download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
    src_file = os.path.join(download_dir, id_val + ".can")
    for _ in range(30):
        if os.path.exists(src_file):
            break
        app.update()
        import time; time.sleep(1)
    if not os.path.exists(src_file):
        messagebox.showerror("Lỗi", f"Không tìm thấy file {id_val}.can trong thư mục Download. Hãy chắc chắn đã tải file xong!")
        
        return None
    try:
        hf.copy_file_by_name(download_dir, feature_folder, id_val + ".can")
        set_status(app,f"Đã copy file về: {save_path}", success=True)
        if auto_open:
            os.startfile(save_path)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể copy/mở file: {e}")
        return None
    return save_path

def refresh_table(app):
    # Xóa tree cũ nếu có
    for widget in app.main_area.winfo_children():
        widget.destroy()

    tk.Label(app.main_area, text="Bảng kiểm tra", font=("Segoe UI", 14, "bold"), bg="white").pack(pady=10)

    # Tạo frame chứa tree và scrollbars
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
        filtered_row = [row[idx] if idx < len(row) and row[idx] is not None else "" for idx in valid_indices]
        filtered_data.append(filtered_row)
    app.data = filtered_data

    # Tạo Treeview
    app.tree = ttk.Treeview(frame, columns=app.headers, show="headings")
    # Định nghĩa tag màu
    app.tree.tag_configure('passed', background='#b6fcb6')      # Xanh lá nhạt
    app.tree.tag_configure('failed', background='#ffb3b3')      # Đỏ nhạt
    app.tree.tag_configure('not_tested', background='#fff7b2')  # Vàng nhạt
    app.tree.tag_configure('discarded', background='#fff7b2')   # Vàng nhạt

    for col in app.headers:
        app.tree.heading(col, text=col)
        app.tree.column(col, width=120)

    # --- Thêm dấu tick khi hiển thị ---
    try:
        crid_idx = app.headers.index("CR Related")
        feature_idx = app.headers.index("Feature")
        id_idx = app.headers.index("Test cases ID")
    except Exception:
        crid_idx = feature_idx = id_idx = None

    # Thêm cột "File existed" nếu cần
    if "File existed" not in app.headers:
        app.headers.append("File existed")

    for row in app.data:
        display_row = [cell if cell is not None else "" for cell in row]
        # Đảm bảo display_row có đủ số cột
        while len(display_row) < len(app.headers):
            display_row.append("")
        # Thêm dấu tick nếu file đã tồn tại
        if crid_idx is not None and feature_idx is not None and id_idx is not None and app.working_dir:
            crid_val = str(display_row[crid_idx]).strip()
            feature_val_raw = str(display_row[feature_idx]).strip()
            id_val = str(display_row[id_idx]).strip()
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
            # Đánh dấu tick vào cột mới "File existed" nếu file đã tồn tại
            if "File existed" not in app.headers:
                app.headers.append("File existed")
            # Đảm bảo display_row có đủ số cột
            while len(display_row) < len(app.headers):
                display_row.append("")
            if os.path.exists(save_path):
                display_row[app.headers.index("File existed")] = "✅"
            else:
                display_row[app.headers.index("File existed")] = ""
        # Xác định tag theo giá trị cột "Test Verdict"
        tag = ""
        try:
            verdict_idx = app.headers.index("Test Verdict")
            verdict = str(display_row[verdict_idx]).strip().lower()
            if verdict == "passed":
                tag = "passed"
            elif verdict == "failed":
                tag = "failed"
            elif verdict in ("not_tested", "discarded"):
                tag = verdict
        except Exception:
            pass
        app.tree.insert("", "end", values=display_row, tags=(tag,))

    # Set lại width các cột nếu có thông tin
    column_widths = getattr(app, "column_widths", None)
    if not column_widths and hasattr(app, "workspace_path"):
        # Thử lấy từ workspace file nếu vừa load
        try:
            with open(app.workspace_path, "r", encoding="utf-8") as f:
                ws_data = json.load(f)
                column_widths = ws_data.get("column_widths", None)
        except Exception:
            column_widths = None
    if column_widths:
        for col in app.headers:
            w = column_widths.get(col, 120)
            app.tree.column(col, width=w)

    # Scroll dọc
    vsb = tk.Scrollbar(frame, orient="vertical", command=app.tree.yview)
    app.tree.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")

    # Scroll ngang
    hsb = tk.Scrollbar(frame, orient="horizontal", command=app.tree.xview)
    app.tree.configure(xscrollcommand=hsb.set)
    hsb.pack(side="bottom", fill="x")

    app.tree.pack(fill="both", expand=True)

    # Bind double click
    app.tree.bind("<Double-1>", lambda event: on_double_click(app, event))
    

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