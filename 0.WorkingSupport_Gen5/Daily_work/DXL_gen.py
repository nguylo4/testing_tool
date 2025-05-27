import os
import re
import subprocess
from tkinter import filedialog, messagebox, Toplevel, scrolledtext, Button
import pandas as pd
from datetime import datetime
from collections import defaultdict
from report_handle import get_project_name

def generate_dxl_testrun(app):
    # Download mapping file nếu chưa có
    mapping_path = os.path.join(app.working_dir, "DAS_RADAR_TestSpec_TestRun_Mapping_Projects_Overview.xls")
    if not os.path.exists(mapping_path):
        download_mapping_excel(app)
    # Đọc template
    template_path = os.path.join(os.path.dirname(__file__), "template", "DXL_template_testrun_gen.can")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    # Group test cases
    groups = group_testcases(app, mapping_path)
    # Sinh code DXL cho từng group
    dxl_all = []
    for key, testcase_ids in groups.items():
        fields = {
            "TestRun_Number": key[0],
            "Owner": key[1],
            "Date_Test": key[2],
            "Release": key[3],
            "HWsample": key[4],
            "test_planned": key[5],
            "Test cases ID": '","'.join(str(i) for i in testcase_ids),
            "Test Verdict": key[6],
            "Error Report": key[7],
            "Comment": key[8]
        }
        dxl_code = template
        for k, v in fields.items():
            dxl_code = dxl_code.replace(f"<{k}>", str(v))
        dxl_all.append(dxl_code)
    # Hiện popup cho phép copy
    from tkinter import Toplevel, scrolledtext, Button, messagebox
    popup = Toplevel(app)
    popup.title("DXL Code - Copy to Clipboard")
    popup.geometry("900x600")
    txt = scrolledtext.ScrolledText(popup, font=("Consolas", 11))
    txt.pack(fill="both", expand=True, padx=10, pady=10)
    txt.insert("1.0", "\n\n".join(dxl_all))
    txt.focus_set()
    def copy_to_clipboard():
        popup.clipboard_clear()
        popup.clipboard_append(txt.get("1.0", "end-1c"))
        messagebox.showinfo("Copied", "Copied all DXL into clipboard!")
    Button(popup, text="Copy All", command=copy_to_clipboard).pack(pady=8)

def download_mapping_excel(app):
    pj_path = r"e:/Projects/DAS_RADAR/30_PRJ/20_REF/REF_Alice_BAS/10_MGMT_SUP/50_PJM_ST/20_Release_Plan/project.pj"
    file_name = "DAS_RADAR_TestSpec_TestRun_Mapping_Projects_Overview.xls"
    dest_path = os.path.join(app.working_dir, file_name)
    cmd = f'si viewrevision --project="{pj_path}" --revision=:member "{file_name}" > "{dest_path}"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Cannot download mapping Excel: {result.stderr}")
    return dest_path

def get_testrun_number(mapping_path, project_name, release, ecuid):
    df = pd.read_excel(mapping_path)
    df1 = df[df["Project and Variant"].astype(str).str.strip() == project_name]
    df1 = df1[df1["Comment"].astype(str).str.contains(str(release), na=False)]

    ecuid_str = str(ecuid).strip().upper()
    rear_numbers = set()
    front_numbers = set()

    # Rear: ECU 0,1,8,9 hoặc ALL_ECUs
    if str(ecuid_str).lower() == "all_ecus" or any(e in ecuid_str for e in ["0", "1", "8", "9"]):
        df_rear = df1[df1["Created View"].astype(str).str.contains("Rear", na=False)]
        if not df_rear.empty:
            rear_numbers.update(str(x) for x in df_rear["Columset No.+E:E"].unique())

    # Front: ECU 2,3 (chỉ khi không phải ALL_ECUs)
    if ecuid_str != "ALL_ECUs" and any(e in ecuid_str for e in ["2", "3"]):
        df_front = df1[df1["Created View"].astype(str).str.contains("Front", na=False)]
        if not df_front.empty:
            front_numbers.update(str(x) for x in df_front["Columset No.+E:E"].unique())

    # Nếu không tìm thấy Rear/Front thì lấy tất cả vào Rear
    if not rear_numbers and not front_numbers and not df1.empty:
        rear_numbers.update(str(x) for x in df1["Columset No.+E:E"].unique())

    return sorted(rear_numbers), sorted(front_numbers)

def get_hw_sample(ecuid):
    ecuid_str = str(ecuid)
    if "8" in ecuid_str or "9" in ecuid_str:
        return "5G3 & 5G5"
    return "5G3"

def get_test_planned(ts_object_status):
    return "Planned" if (ts_object_status == "Accepted by project" or ts_object_status == "Ready for review")  else ""

def get_comment(test_scope, release):
    if "regression" in test_scope.lower():
        return f"[Regression {release}]"
    return ""

def group_testcases(app, mapping_path):
    idx = {h: i for i, h in enumerate(app.headers)}
    groups = defaultdict(list)
    for row in app.data:
        ts_object_status = row[idx["TS_ObjectStatus"]]
        if str(ts_object_status).strip() == "Discarded by project":
            continue

        project_name = get_project_name(app.project)
        release = row[idx["Release"]]
        ecuid = str(row[idx["ECU ID"]]).strip().lower()
        rear_numbers, front_numbers = get_testrun_number(mapping_path, project_name, release, ecuid)
        owner = row[idx["Owner"]]
        date_test = datetime.today().strftime("%Y-%m-%d")
        hw_sample = get_hw_sample(ecuid)
        test_planned = get_test_planned(ts_object_status)
        test_verdict = row[idx["Test Verdict"]]
        error_report = row[idx["Error Report"]]
        test_scope = row[idx["Test scope"]]
        comment = get_comment(test_scope, release)
        testcase_id = row[idx["Test cases ID"]]

        # Xác định group cho Rear nếu có 0,1,8,9 hoặc ALL_ECUs
        if ecuid == "all_ecus" or any(e in ecuid for e in ["0", "1", "8", "9"]):
            for testrun_number in rear_numbers:
                key = (testrun_number, owner, date_test, release, hw_sample, test_planned, test_verdict, error_report, comment)
                groups[key].append(testcase_id)
        # Xác định group cho Front nếu có 2,3
        if any(e in ecuid for e in ["2", "3"]):
            for testrun_number in front_numbers:
                key = (testrun_number, owner, date_test, release, "5G3", test_planned, test_verdict, error_report, comment)
                groups[key].append(testcase_id)
    return groups