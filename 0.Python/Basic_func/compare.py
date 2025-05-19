import tempfile
import subprocess
from tkinter import messagebox, ttk
import tkinter as tk
import os
from file_ops import set_status, ensure_script_file, refresh_table
import tksheet

def compare_content_requirement(app):
    # Thêm cột "Check Consistency" nếu chưa có
    if "Check Consistency" not in app.headers:
        app.headers.append("Check Consistency")
        for row in app.data:
            row.append("")

    selected = app.sheet.get_selected_cells()
    if not selected:
        messagebox.showwarning("Chọn dòng", "Hãy chọn một dòng trong bảng!")
        return
    else:
        row_idx, _ = list(selected)[0]
        row = app.sheet.get_row_data(row_idx)

    try:
        req_id_idx = app.headers.index("Requirement ID")
        content_idx = app.headers.index("Content Requirement")
        design_idx = app.headers.index("TS_TestDesciption")
        check_idx = app.headers.index("Check Consistency")
        check_TCidx = app.headers.index("Test cases ID")
    except ValueError:
        messagebox.showerror("Lỗi", "Không tìm thấy cột cần thiết!")
        return

    values = row
    save_path = ensure_script_file(app, values, auto_open=False)
    if not save_path or not os.path.exists(save_path):
        row[check_idx] = "CHECK"
        refresh_table(app)
        return

    req_id = str(row[req_id_idx]).strip()
    content_requirement = str(row[content_idx]).strip()
    test_design = str(row[design_idx]).strip()

    # Đọc nội dung file và trích xuất đoạn cần so sánh
    try:
        with open(save_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        start_marker = f"[{req_id}]"
        start_idx = file_content.find(start_marker)
        if start_idx == -1:
            row[check_idx] = "CHECK"
            refresh_table(app)
            return
        end_idx = file_content.find("------------------------", start_idx)
        if end_idx == -1:
            end_idx = len(file_content)
        file_requirement_content = file_content[start_idx:end_idx].strip()

        # Lấy đoạn giữa @Test design và */
        testcase_id = str(row[check_TCidx]).strip()
        testcase_marker = "*/"
        design_start = file_content.find("@Test design")
        if design_start != -1:
            design_end = file_content.find(testcase_marker, design_start)
            if design_end == -1:
                design_end = len(file_content)
            file_design_content = file_content[design_start + len("@Test design"):design_end].strip()
        else:
            file_design_content = ""
    except Exception:
        row[check_idx] = "CHECK"
        refresh_table(app)
        return

    # Lưu 2 đoạn ra file tạm để so sánh bằng Beyond Compare
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f1, \
         tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f2:
        f1.write(content_requirement + "\n Test design:" + test_design)
        f1_path = f1.name
        f2.write(file_requirement_content + "\n Test design:" + file_design_content)
        f2_path = f2.name

    try:
        subprocess.Popen([r'C:\Program Files\Beyond Compare 4\BCompare.exe', f1_path, f2_path])
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở Beyond Compare: {e}")
        row[check_idx] = "CHECK"
        refresh_table(app)
        return

    # Hiện popup để bạn chọn kết quả
    status = ask_consistency_status(app)
    row[check_idx] = status
    # Cập nhật lại dòng đã sửa vào app.data
    app.data[row_idx] = row
    refresh_table(app)
    set_status(app, "Đã kiểm tra xong dòng đã chọn!", success=True)

def ask_consistency_status(app):
    win = tk.Toplevel(app)
    win.title("Chọn kết quả kiểm tra")
    win.geometry("300x120")
    tk.Label(win, text="Kết quả kiểm tra file này là gì?", font=("Segoe UI", 11)).pack(pady=10)
    result = {"value": None}
    def set_result(val):
        result["value"] = val
        win.destroy()
    btn_frame = tk.Frame(win)
    btn_frame.pack(pady=10)
    ttk.Button(btn_frame, text="OK", width=8, command=lambda: set_result("OK")).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="NOK", width=8, command=lambda: set_result("NOK")).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="CHECK", width=8, command=lambda: set_result("CHECK")).pack(side="left", padx=5)
    win.grab_set()
    win.wait_window(win)
    return result["value"]