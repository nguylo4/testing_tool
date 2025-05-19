import tempfile
import subprocess
from tkinter import messagebox, ttk
import tkinter as tk
import os
from file_ops import set_status, refresh_table
from script_handle import ensure_script_file
import tksheet

def compare_content_requirement(app):
    if not hasattr(app, "sheet") or app.sheet is None:
        messagebox.showwarning("No table", "No table loaded!")
        return
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
        messagebox.showwarning("Can not found", "File script is not existed!")
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
        f1.write("IN SSRS:\n"+content_requirement + "\n Test design:" + test_design)
        f1_path = f1.name
        f2.write("IN SCRIPT\n"+file_requirement_content + "\n Test design:" + file_design_content)
        f2_path = f2.name
        # print("debug: tạo file tạm thành công")

    try:
        bcompare_path = find_bcompare_exe()
        if not bcompare_path:
            messagebox.showerror("Error", "Cannot find BCompare.exe!")
            row[check_idx] = "CHECK"
            refresh_table(app)
            return
        subprocess.Popen([bcompare_path, f1_path, f2_path])
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open Beyond Compare: {e}")
        row[check_idx] = "CHECK"
        refresh_table(app)
        return

    # Hiện popup để bạn chọn kết quả
    status = ask_consistency_status(app)
    row[check_idx] = status
    # Cập nhật lại dòng đã sửa vào app.data
    app.data[row_idx] = row
    refresh_table(app)
    set_status(app, "Checking completed!", success=True)

def compare_ssrs_vs_spec(app):
    if not hasattr(app, "sheet") or app.sheet is None:
        messagebox.showwarning("No table", "No table loaded!")
        return
    # Thêm cột "Consistency SSRS vs Spec" nếu chưa có
    if "Consistency SSRS vs Spec" not in app.headers:
        app.headers.append("Consistency SSRS vs Spec")
        for row in app.data:
            row.append("")

    selected = app.sheet.get_selected_cells()
    if not selected:
        messagebox.showwarning("Select row", "Please select a row!")
        return
    else:
        row_idx, _ = list(selected)[0]
        row = app.sheet.get_row_data(row_idx)

    try:
        content_idx = app.headers.index("Content Requirement")
        reqtext_idx = app.headers.index("Requirement text")
        check_idx = app.headers.index("Consistency SSRS vs Spec")
    except ValueError:
        messagebox.showerror("Error", "Can not found colum 'Content Requirement' or 'Requirement text' or 'Consistency SSRS vs Spec'!")
        return

    content_requirement = str(row[content_idx]).strip()
    requirement_text = str(row[reqtext_idx]).strip()

    # Lưu 2 đoạn ra file tạm để so sánh bằng Beyond Compare
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f1, \
         tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt", encoding="utf-8") as f2:
        f1.write("IN SPEC:\n"+content_requirement)
        f1_path = f1.name
        f2.write("IN SSRS:\n"+requirement_text)
        f2_path = f2.name

    try:
        bcompare_path = find_bcompare_exe()
        if not bcompare_path:
            messagebox.showerror("Error", "Cannot find BCompare.exe!")
            row[check_idx] = "CHECK"
            refresh_table(app)
            return
        subprocess.Popen([bcompare_path, f1_path, f2_path])
    except Exception as e:
        messagebox.showerror("Eror", f"Cannot open Beyond Compare: {e}")
        row[check_idx] = "CHECK"
        refresh_table(app)
        return

    # Hiện popup để bạn chọn kết quả
    status = ask_consistency_status(app)
    row[check_idx] = status
    app.data[row_idx] = row
    refresh_table(app)
    set_status(app, "Checking completed!", success=True)
import shutil

def find_bcompare_exe():
    # Thử tìm trong PATH
    exe = shutil.which("BCompare.exe")
    if exe:
        return exe

    # Thử các vị trí cài đặt phổ biến
    possible_paths = [
        r"C:\Program Files\Beyond Compare 4\BCompare.exe",
        r"C:\Program Files (x86)\Beyond Compare 4\BCompare.exe",
        r"C:\Program Files\Beyond Compare 3\BCompare.exe",
        r"C:\Program Files (x86)\Beyond Compare 3\BCompare.exe",
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path

    # Nếu vẫn không thấy, hỏi người dùng chọn file exe
    from tkinter import filedialog
    exe = filedialog.askopenfilename(
        title="Select Beyond Compare (BCompare.exe)",
        filetypes=[("Beyond Compare", "BCompare.exe")],
    )
    return exe if exe else None

def ask_consistency_status(app):
    win = tk.Toplevel(app)
    win.title("Choose result of checking")
    win.geometry("300x120")
    tk.Label(win, text="Checking OK or NOT?", font=("Segoe UI", 11)).pack(pady=10)
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