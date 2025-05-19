import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
import os
import re

passed_count = 0
failed_count = 0

def list_files_in_directory(directory):
    file_list = []
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)) and not any(keyword in filename for keyword in ["Frame", ".css", "info"]):
            file_list.append(filename)
    return file_list

def select_directory():
    selected_directory = filedialog.askdirectory()
    if selected_directory:
        entry_path.delete(0, tk.END)
        entry_path.insert(0, selected_directory)
        display_files(selected_directory)

def select_output_directory():
    selected_output_directory = filedialog.askdirectory()
    if selected_output_directory:
        output_entry.delete(0, tk.END)
        output_entry.insert(0, selected_output_directory)

def display_files(directory):
    files = list_files_in_directory(directory)
    file_listbox.delete(0, tk.END)
    for file in files:
        file_listbox.insert(tk.END, file)

def get_verdict(file_content):
    if 'TestcaseHeadingNegativeResult' in file_content:
        return "Failed"
    elif 'TestcaseHeadingPositiveResult' in file_content:
        return "Passed"
    else:
        return "Unknown"

def extract_test_case_name(file_content):
    pattern = r'<a\s+name="[^"]+">Test\s+Case\s+([^:]+):'
    match = re.search(pattern, file_content)
    if match:
        return match.group(1)
    return "Unknown"

def read_file_content(file_path):
    if os.path.isfile(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    return None

def open_output_folder():
    output_directory = output_entry.get()
    if os.path.isdir(output_directory):
        os.startfile(output_directory)
    else:
        messagebox.showerror("Lỗi", "Thư mục đầu ra không tồn tại.")

def export_to_html_report(passed=True, failed=True):
    global passed_count, failed_count
    input_directory = entry_path.get()
    output_directory = output_entry.get()
    if not os.path.isdir(input_directory):
        messagebox.showerror("Lỗi", "Đường dẫn thư mục đầu vào không tồn tại hoặc không phải là một thư mục.")
        return
    if not os.path.isdir(output_directory):
        messagebox.showerror("Lỗi", "Đường dẫn thư mục đầu ra không tồn tại hoặc không phải là một thư mục.")
        return


    # Đọc nội dung của file Frame_Report.html
    frame_report_path = os.path.join(input_directory, "Frame_Report.html")
    frame_report_content = read_file_content(frame_report_path)
    if frame_report_content is None:
        messagebox.showerror("Lỗi", "Không tìm thấy file Frame_Report.html trong thư mục đầu vào.")
        return

    # Đọc nội dung của file extendedNavigation.css
    css_path = os.path.join(input_directory, "extendedNavigation.css")
    css_content = read_file_content(css_path)
    if css_content is None:
        messagebox.showerror("Lỗi", "Không tìm thấy file extendedNavigation.css trong thư mục đầu vào.")
        return


    # Tạo thư mục Passed và Failed nếu chưa tồn tại
    passed_directory = os.path.join(output_directory, "Passed")
    failed_directory = os.path.join(output_directory, "Failed")
    os.makedirs(passed_directory, exist_ok=True)
    os.makedirs(failed_directory, exist_ok=True)

    success_count = 0
    failed_files = []
    passed_files_list = []
    failed_files_list = []
    for filename in list_files_in_directory(input_directory):
        file_path = os.path.join(input_directory, filename)
        file_content = read_file_content(file_path)
        if file_content is None:
            messagebox.showwarning("Cảnh báo", f"Không thể đọc file {filename}.")
            continue
        verdict = get_verdict(file_content)

        # Xác định thư mục đích
        if verdict == "Passed" and passed:
            destination_directory = passed_directory
            passed_count += 1
        elif verdict == "Failed" and failed:
            destination_directory = failed_directory
            failed_count += 1
        else:
            continue



        # Xác định tên cho file output
        test_case_name = extract_test_case_name(file_content)
        output_file_name = f"{test_case_name}.html"

        if verdict == "Passed" and passed:
            destination_directory = passed_directory
            passed_files_list.append(test_case_name)
            passed_count += 1
        elif verdict == "Failed" and failed:
            destination_directory = failed_directory
            failed_files_list.append(test_case_name)
            failed_count += 1
        else:
            continue


        # Đường dẫn đầy đủ của file output
        output_file_path = os.path.join(destination_directory, output_file_name)

       # Loại bỏ phần Test Overview
        updated_frame_report_content = re.sub(r'<a\s+name="TestOverview">.*?<a\s+name="TestModuleInfo">', '', frame_report_content, flags=re.DOTALL)

        content_pass='''    
        <a name="TOP"></a>
            <table class="HeadingTable">
            <tr>
                <td>
                <big class="Heading1">Report: SWT_CC</big>
                </td>
            </tr>
            </table>
            <center>
            <table class="OverallResultTable">
                <tr>
                <td class="PositiveResult">Test passed</td>
                </tr>
            </table>
            </center>
            <a name="GeneralTestInfo">
                    '''
        content_fail='''    
        <a name="TOP"></a>
            <table class="HeadingTable">
            <tr>
                <td>
                <big class="Heading1">Report: SWT_CC</big>
                </td>
            </tr>
            </table>
            <center>
            <table class="OverallResultTable">
                <tr>
                <td class="NegativeResult">Test failed</td>
                </tr>
            </table>
            </center>
            <a name="GeneralTestInfo"></a>
                    '''

        # Thay đổi nội dung dựa trên verdict của test case
        if verdict == "Passed" and passed:
            # Thay thế class TestcaseHeadingNegativeResult thành TestcaseHeadingPositiveResult
            updated_report_content = re.sub(r'<a\s+name="TOP">.*?<a\s+name="GeneralTestInfo"></a>', content_pass, updated_frame_report_content, flags=re.DOTALL)

        elif verdict == "Failed" and failed:
            # Thay thế class TestcaseHeadingPositiveResult thành TestcaseHeadingNegativeResult
            updated_report_content = re.sub(r'<a\s+name="TOP">.*?<a\s+name="GeneralTestInfo"></a>', content_fail, updated_frame_report_content, flags=re.DOTALL)

        else:
            updated_report_content = updated_frame_report_content

        # Tạo nội dung cho file output

        End_of_report='''
        <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd>
        <html>
            <body>
                <table class="SubHeadingTable">
                    <tr>
                        <td>
                        <div class="Heading2">End of Report</div>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
                    '''

        output_content = f"<style>{css_content}</style>\n{updated_report_content}\n{file_content}\n{End_of_report}"

        # Ghi nội dung vào file output
        try:
            with open(output_file_path, 'w') as output_file:
                output_file.write(output_content)

            success_count += 1
        except Exception as e:
            failed_files.append(filename)


    if success_count == len(list_files_in_directory(input_directory)):
        messagebox.showinfo("Thông báo", "Xuất HTML report thành công cho tất cả các file.")
    elif success_count == 0:
        messagebox.showerror("Lỗi", "Xuất HTML report thất bại cho tất cả các file.")
    else:
        messagebox.showinfo("Thông báo", f"Xuất HTML report thành công cho {success_count} file. Xuất thất bại cho {len(failed_files)} file.")
        if failed_files:
            messagebox.showinfo("Danh sách file xuất thất bại", "\n".join(failed_files))

    passed_files_listbox.delete(0, tk.END)
    failed_files_listbox.delete(0, tk.END)
    for file in passed_files_list:
        passed_files_listbox.insert(tk.END, file)
    for file in failed_files_list:
        failed_files_listbox.insert(tk.END, file)

entry_path = tk.Entry(Split_HMTL, width=50)
entry_path.grid(row=1, column=1, padx=5, pady=5)

failed_files_listbox = tk.Listbox(Split_HMTL, width=50)
failed_files_listbox.grid(row=10, column=1, padx=5, pady=5)

passed_files_listbox = tk.Listbox(Split_HMTL, width=50)
passed_files_listbox.grid(row=10, column=0, padx=5, pady=5)