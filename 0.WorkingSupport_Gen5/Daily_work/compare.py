import tempfile
import subprocess
from tkinter import messagebox, ttk
import tkinter as tk
import os
from file_ops import set_status, ensure_script_file, refresh_table
import tksheet

def compare_content_requirement(app):
    # Thêm cột "Check Consistency" nếu chưa có
    if "Consistency Spec vs Script" not in app.headers:
        app.headers.append("Consistency Spec vs Script")
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
        design_idx = app.headers.index("TS_TestDescription")
        check_idx = app.headers.index("Consistency Spec vs Script")
        check_TCidx = app.headers.index("Test cases ID")
    except ValueError:
        messagebox.showerror("Lỗi", "Không tìm thấy cột cần thiết!")
        return

    values = row
    save_path = ensure_script_file(app, values, auto_open=False)
    if not save_path or not os.path.exists(save_path):
        # print("debug: file script không tồn tại")
        messagebox.showwarning("Không tìm thấy file", "File script không tồn tại!")
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
    except UnicodeDecodeError:
        try:
            with open(save_path, "r", encoding="utf-8-sig") as f:
                file_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(save_path, "r", encoding="latin1") as f:
                    file_content = f.read()
            except Exception as e:
                # print(f"debug: không thể đọc file script: {e}")
                messagebox.showerror("Lỗi đọc file script", f"Không thể đọc file script:\n{e}")
                row[check_idx] = "CHECK"
                refresh_table(app)
                return

    start_marker = f"[{req_id}]"
    start_idx = file_content.find(start_marker)
    if start_idx == -1:
        # print("debug: không tìm thấy requirement")
        messagebox.showwarning("Không tìm thấy requirement", f"Không tìm thấy [{req_id}] trong file script!")
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
    # Tìm vị trí bắt đầu của phần test design với nhiều biến thể
    design_markers = [
        "@Test", "@test", "@design", "@Design"
    ]
    design_start = -1
    file_design_content = ""
    for marker in design_markers:
        design_start = file_content.find(marker)
        if design_start != -1:
            design_end = file_content.find(testcase_marker, design_start-len(marker))
            if design_end == -1:
                design_end = len(file_content)
            file_design_content = file_content[design_start + len(marker):design_end].strip()
            break  # Dừng ngay khi tìm thấy marker đầu tiên

    # Lưu 2 đoạn ra file tạm để so sánh bằng Beyond Compare
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f1, \
         tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f2:
        f1.write(content_requirement + "\n Test design:" + test_design)
        f1_path = f1.name
        f2.write(file_requirement_content + "\n Test design:" + file_design_content)
        f2_path = f2.name
        # print("debug: tạo file tạm thành công")

    try:
        subprocess.Popen([r'C:\Program Files\Beyond Compare 4\BCompare.exe', f1_path, f2_path])
        # print("debug: mở Beyond Compare thành công")
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

def compare_ssrs_vs_spec(app):
    # Thêm cột "Consistency SSRS vs Spec" nếu chưa có
    if "Consistency SSRS vs Spec" not in app.headers:
        app.headers.append("Consistency SSRS vs Spec")
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
        content_idx = app.headers.index("Content Requirement")
        reqtext_idx = app.headers.index("Requirement text")
        check_idx = app.headers.index("Consistency SSRS vs Spec")
    except ValueError:
        messagebox.showerror("Lỗi", "Không tìm thấy cột cần thiết!")
        return

    content_requirement = str(row[content_idx]).strip()
    requirement_text = str(row[reqtext_idx]).strip()

    # Lưu 2 đoạn ra file tạm để so sánh bằng Beyond Compare
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f1, \
         tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f2:
        f1.write(content_requirement)
        f1_path = f1.name
        f2.write(requirement_text)
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