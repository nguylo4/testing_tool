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
        f1.write("IN SSRS:\n"+content_requirement)
        f1_path = f1.name
        f2.write("IN SPEC:\n"+requirement_text)
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
    ttk.Button(btn_frame, bootstyle="success", text="OK", width=8, command=lambda: set_result("OK")).pack(side="left", padx=5)
    ttk.Button(btn_frame, bootstyle="danger",text="NOK", width=8, command=lambda: set_result("NOK")).pack(side="left", padx=5)
    ttk.Button(btn_frame, bootstyle="warning",text="CHECK", width=8, command=lambda: set_result("CHECK")).pack(side="left", padx=5)
    win.grab_set()
    win.wait_window(win)
    return result["value"]

# def compare_feature_columns(app):
#     if not hasattr(app, "sheet") or app.sheet is None:
#         messagebox.showwarning("No table", "No table loaded!")
#         return
#     try:
#         h_feature_idx = app.headers.index("H_Feature")
#         spec_feature_idx = app.headers.index("Feature_in_Spec")
#     except ValueError:
#         messagebox.showerror("Error", "Không tìm thấy cột 'H_Feature' hoặc 'Feature_in_Spec'!")
#         return

#     for row_idx, row in enumerate(app.data):
#         h_val = str(row[h_feature_idx]).strip() if row[h_feature_idx] is not None else ""
#         spec_val = str(row[spec_feature_idx]).strip() if row[spec_feature_idx] is not None else ""
#         # Nếu một trong hai ô không có dữ liệu
#         if not h_val and not spec_val:
#             continue  # Bỏ qua nếu cả hai đều rỗng
#         if not h_val:
#             app.sheet.highlight_cells(row=row_idx, column=h_feature_idx, bg="#ffb3b3")
#         if not spec_val:
#             app.sheet.highlight_cells(row=row_idx, column=spec_feature_idx, bg="#ffb3b3")
#         # Nếu cả hai đều có dữ liệu nhưng khác nhau
#         if h_val and spec_val and h_val != spec_val:
#             app.sheet.highlight_cells(row=row_idx, column=h_feature_idx, bg="#ffb3b3")
#             app.sheet.highlight_cells(row=row_idx, column=spec_feature_idx, bg="#ffb3b3")

def compare_attribute(app):
    # Tạo cột "compare attribute" nếu chưa có
    if "compare attribute" not in app.headers:
        app.headers.append("compare attribute")
        for row in app.data:
            row.append("")
    compare_idx = app.headers.index("compare attribute")

    # Lấy index các cột cần thiết
    def idx(col): 
        try: return app.headers.index(col)
        except: return None

    idxs = {
        "H_Feature": idx("H_Feature"),
        "Feature_in_Spec": idx("Feature_in_Spec"),
        "CR ID": idx("CR ID"),
        "TS_RefToRequirement": idx("TS_RefToRequirement"),
        "H_SafetyClassification": idx("H_SafetyClassification"),
        "TS_TestPriority": idx("TS_TestPriority"),
        "H_FailureConsequense": idx("H_FailureConsequense"),
        "TS_RefToAutomation": idx("TS_RefToAutomation"),
        "Test cases ID": idx("Test cases ID"),
        "TS_StateOfAutomation": idx("TS_StateOfAutomation"),
        "TS_TestSet": idx("TS_TestSet"),
        "TS_SW_TestEnvironment": idx("TS_SW_TestEnvironment"),
        "Requirement Status": idx("Requirement Status"),
        "TS_ObjectStatus": idx("TS_ObjectStatus"),
    }

    for row_idx, row in enumerate(app.data):
        results = []

        # 1. Compare Feature
        h_feat = str(row[idxs["H_Feature"]]).strip() if idxs["H_Feature"] is not None else ""
        spec_feat = str(row[idxs["Feature_in_Spec"]]).strip() if idxs["Feature_in_Spec"] is not None else ""
        if h_feat and spec_feat:
            results.append(f"Feature: {'ok\n' if h_feat == spec_feat else 'not ok\n'}")
        elif not h_feat or not spec_feat:
            results.append("Feature: not ok\n")

        # 2. CR ID in TS_RefToRequirement
        crid = str(row[idxs["CR ID"]]).strip() if idxs["CR ID"] is not None else ""
        ref_req = str(row[idxs["TS_RefToRequirement"]]).strip() if idxs["TS_RefToRequirement"] is not None else ""
        if crid and ref_req:
            results.append(f"TS_RefToRequirement: {'ok\n' if crid in ref_req else 'not ok\n'}")
        else:
            results.append("TS_RefToRequirement: not ok\n")

        # 3. SafetyClassification & Priority
        safety = str(row[idxs["H_SafetyClassification"]]).strip() if idxs["H_SafetyClassification"] is not None else ""
        priority = str(row[idxs["TS_TestPriority"]]).strip().lower() if idxs["TS_TestPriority"] is not None else ""
        fail_cons = str(row[idxs["H_FailureConsequense"]]).strip().lower() if idxs["H_FailureConsequense"] is not None else ""
        if "asil" in safety.lower():
            results.append(f"Priority: {'ok\n' if priority == 'high' else 'not ok\n'}")
        else:
            results.append(f"Priority: {'ok\n' if priority == fail_cons else 'not ok\n'}")

        # 4. TS_RefToAutomation path check
        ref_auto = str(row[idxs["TS_RefToAutomation"]]).strip() if idxs["TS_RefToAutomation"] is not None else ""
        feat = h_feat
        feat = app.feature_map.get(feat, feat)
        tcid = str(row[idxs["Test cases ID"]]).strip() if idxs["Test cases ID"] is not None else ""
        expected_path = f"e:/Projects/DAS_RADAR/30_PRJ/10_CUST/10_VAG/{app.project}/60_ST/{app.Test_level}/20_SWT_CC/10_Debugger_Test/20_Scripts/Test_Cases/{feat}/{tcid}.can"
        
        def normalize_path(s):
            return s.replace("\\", "/").strip().lower()
    
        if ref_auto:
            if normalize_path(ref_auto) == normalize_path(expected_path):
                results.append("TS_RefToAutomation: ok\n")
            else:
                results.append("TS_RefToAutomation: not ok\n")
        else:
            results.append("TS_RefToAutomation: not ok\n") 

        # 5. TS_StateOfAutomation must have "Implemented"
        state_auto = str(row[idxs["TS_StateOfAutomation"]]).strip().lower() if idxs["TS_StateOfAutomation"] is not None else ""
        if state_auto:
            results.append(f"TS_StateOfAutomation: {'ok\n' if 'implemented' in state_auto else 'not ok\n'}")

        # 6. TS_TestSet must have Extended test or Basic test
        testset = str(row[idxs["TS_TestSet"]]).strip().lower() if idxs["TS_TestSet"] is not None else ""
        if testset:
            results.append(f"TS_TestSet: {'ok\n' if ('extended test' in testset or 'basic test' in testset) else 'not ok\n'}")
        else:
            results.append("TS_TestSet: not ok\n")

        # 7. TS_SW_TestEnvironment must have Debugger Test
        env = str(row[idxs["TS_SW_TestEnvironment"]]).strip().lower() if idxs["TS_SW_TestEnvironment"] is not None else ""
        if env:
            results.append(f"TS_SW_TestEnvironment: {'ok\n' if 'debugger test' in env else 'not ok\n'}")
        else:
            results.append("TS_SW_TestEnvironment: not ok\n")

        # 8. Requirement Status & TS_ObjectStatus
        req_status = str(row[idxs["Requirement Status"]]).strip().lower() if idxs["Requirement Status"] is not None else ""
        obj_status = str(row[idxs["TS_ObjectStatus"]]).strip().lower() if idxs["TS_ObjectStatus"] is not None else ""
        if any(x in req_status for x in ["discarded", "false, Discarded", "False"]):
            results.append(f"TS_ObjectStatus: {'ok\n' if obj_status == 'Discarded by project' else 'need check\n'}")


        # Ghi kết quả vào cột "compare attribute" cho từng dòng
        row[compare_idx] = "; ".join(results)

    # Refresh bảng trước khi highlight
    refresh_table(app)

    # Highlight sau khi bảng đã được tạo lại
    for row_idx, row in enumerate(app.data):
        cell_value = row[compare_idx].lower()
        if "not ok" in cell_value or "check" in cell_value:
            app.sheet.highlight_cells(row=row_idx, column=compare_idx, bg="#fff7b2")  # vàng nhạt
        else:
            app.sheet.highlight_cells(row=row_idx, column=compare_idx, bg="#b6fcb6")  # xanh nhạt