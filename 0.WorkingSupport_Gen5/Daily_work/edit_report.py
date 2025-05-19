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
 
def select_directory(app):
    selected_directory = filedialog.askdirectory()
    if selected_directory:
        app.entry_path.delete(0, tk.END)
        app.entry_path.insert(0, selected_directory)
        display_files(selected_directory)

def select_output_directory(app):
    selected_output_directory = filedialog.askdirectory()
    if selected_output_directory:
        app.output_entry.delete(0, tk.END)
        app.output_entry.insert(0, selected_output_directory)
 
def display_files(app,directory):
    files = list_files_in_directory(directory)
    app.file_listbox.delete(0, tk.END)
    for file in files:
        app.file_listbox.insert(tk.END, file)

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

def open_output_folder(app):
    output_directory = app.output_entry.get()
    if os.path.isdir(output_directory):
        os.startfile(output_directory)
    else:
        messagebox.showerror("Lỗi", "Thư mục đầu ra không tồn tại.")

def export_to_html_report(app,passed=True, failed=True):
    global passed_count, failed_count
    input_directory = app.entry_path.get()
    output_directory = app.output_entry.get()
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

    app.passed_files_listbox.delete(0, tk.END)
    app.failed_files_listbox.delete(0, tk.END)
    for file in passed_files_list:
        app.passed_files_listbox.insert(tk.END, file)
    for file in failed_files_list:
        app.failed_files_listbox.insert(tk.END, file)

class HTMLMergerApp:
    def __init__(self, parent_frame):
        self.frame = ttk.Frame(parent_frame)
        self.frame.pack(pady=20, fill='both', expand=True)

        self.select_btn = tk.Button(
            self.frame, text="Chọn Thư Mục", command=self.select_directory
        )
        self.select_btn.pack(pady=5)

        self.tree = ttk.Treeview(self.frame)
        self.tree.pack(pady=10, fill='both', expand=True)

        self.merge_all_btn = tk.Button(
            self.frame, text="Merge All", command=self.merge_all_files
        )
        self.merge_all_btn.pack(side=tk.LEFT, padx=5)
        self.merge_all_btn.config(state=tk.DISABLED)

        self.merge_selected_btn = tk.Button(
            self.frame, text="Merge Selected", command=self.merge_selected_files
        )
        self.merge_selected_btn.pack(side=tk.RIGHT, padx=5)
        self.merge_selected_btn.config(state=tk.DISABLED)

        self.status_label = tk.Label(self.frame, text="", fg="green")
        self.status_label.pack(pady=10)

        self.test_cases = {}

    def select_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.directory = directory
            self.find_test_cases()
            if self.test_cases:
                self.merge_all_btn.config(state=tk.NORMAL)
                self.merge_selected_btn.config(state=tk.NORMAL)
            else:
                self.merge_all_btn.config(state=tk.DISABLED)
                self.merge_selected_btn.config(state=tk.DISABLED)

    def find_test_cases(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.test_cases = {}
        pattern = re.compile(r"SwT_VW_02_(\d+)_(.+)\.html")
        merged_pattern = re.compile(r"SwT_VW_02_(\d+)_merged\.html")
        for filename in os.listdir(self.directory):
            if merged_pattern.match(filename):
                continue
            match = pattern.match(filename)
            if match:
                case_id = match.group(1)
                part = match.group(2)
                if case_id not in self.test_cases:
                    self.test_cases[case_id] = []
                self.test_cases[case_id].append((part, filename))
        for case_id, parts in list(self.test_cases.items()):
            if len(parts) > 1:
                parent_id = self.tree.insert(
                    "", "end", text=f"Test Case ID: {case_id}", open=False
                )
                for part, filename in sorted(parts, key=lambda x: x[0]):
                    self.tree.insert(parent_id, "end", text=filename, value=filename)
            else:
                del self.test_cases[case_id]

    def get_verdict(self, file_content):
        pattern = r'<td class="NegativeResult">Test failed</td>'
        match = re.search(pattern, file_content)
        return "Failed" if match else "Passed"

    def merge_files(self, selected_cases):
        try:
            for case_id in selected_cases:
                merged_html = ""
                verdicts = []
                parts = self.test_cases[case_id]
                parts.sort(key=lambda x: x[0])
                first_file = True
                last_file = parts[-1][1]
                for part, filename in parts:
                    with open(
                        os.path.join(self.directory, filename), "r", encoding="utf-8"
                    ) as file:
                        content = file.read()
                        part_name = part.replace("_", " ")
                        content = content.replace(
                            '<big class="Heading2">Test Case Details</big>',
                            f'<big class="Heading2">Test Case Details for {part_name}</big>',
                        )
                        if filename != last_file:
                            content = re.sub(
                                r'<table class="GroupEndTable">.*?</table>',
                                "",
                                content,
                                flags=re.DOTALL,
                            )
                            content = re.sub(
                                r'<table class="SubHeadingTable">\s*<tr>\s*<td>\s*<div class="Heading2">End of Report</div>\s*</td>\s*</tr>\s*</table>',
                                "",
                                content,
                                flags=re.DOTALL,
                            )
                        if first_file:
                            merged_html += content
                            first_file = False
                        else:
                            start_index = content.find('<a name="TestModuleInfo"></a>')
                            if start_index != -1:
                                partial_content = content[start_index:]
                                merged_html += (
                                    "</script>\n  </head>\n  <body>\n" + partial_content
                                )
                        verdict = self.get_verdict(content)
                        verdicts.append(verdict)
                overall_verdict = "Failed" if "Failed" in verdicts else "Passed"
                output_filename = f"SwT_VW_02_{case_id}_merged.html"
                with open(
                    os.path.join(self.directory, output_filename), "w", encoding="utf-8"
                ) as output_file:
                    output_file.write(merged_html)
                    content_pass = """    
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
                    """
                    content_fail = """    
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
                    """
                    with open(
                        os.path.join(self.directory, output_filename), "r", encoding="utf-8"
                    ) as file:
                        output_file_content = file.read()
                    if overall_verdict == "Passed":
                        updated_report_content = re.sub(
                            r'<a\s+name="TOP">.*?<a\s+name="GeneralTestInfo"></a>',
                            content_pass,
                            output_file_content,
                            flags=re.DOTALL,
                        )
                    elif overall_verdict == "Failed":
                        updated_report_content = re.sub(
                            r'<a\s+name="TOP">.*?<a\s+name="GeneralTestInfo"></a>',
                            content_fail,
                            output_file_content,
                            flags=re.DOTALL,
                        )
                    else:
                        updated_report_content = output_file_content
                    with open(
                        os.path.join(self.directory, output_filename), "w", encoding="utf-8"
                    ) as file:
                        file.write(updated_report_content)
            self.status_label.config(text="Đã gộp các file thành công!", fg="green")
            messagebox.showinfo("Thành công", "Đã gộp các file thành công!")
        except Exception as e:
            self.status_label.config(text=f"Gộp file thất bại: {e}", fg="red")
            messagebox.showerror("Lỗi", f"Gộp file thất bại: {e}")

    def merge_all_files(self):
        self.merge_files(self.test_cases.keys())

    def merge_selected_files(self):
        selected_items = self.tree.selection()
        selected_cases = set()
        for item in selected_items:
            parent = self.tree.parent(item)
            if parent:
                case_id = self.tree.item(parent, "text").split(": ")[1]
            else:
                case_id = self.tree.item(item, "text").split(": ")[1]
            selected_cases.add(case_id)
        self.merge_files(selected_cases)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.tooltip = None

    def show_tooltip(self, event):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(self.tooltip, text=self.text, background="yellow", relief="solid", borderwidth=1, padx=5, pady=5)
        label.pack()

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, directory)
        list_files()

def browse_excel_file():
    filepath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
    if filepath:
        excel_entry.delete(0, tk.END)
        excel_entry.insert(0, filepath)

def list_files():
    folder_path = directory_entry.get()
    extension = ext_entry.get()
    if not folder_path or not extension:
        return
    files = [f for f in os.listdir(folder_path) if f.endswith(extension)]
    current_files_listbox.delete(0, tk.END)
    for file in files:
        file_name = os.path.splitext(file)[0]
        current_files_listbox.insert(tk.END, file_name)
    update_preview_list()

def update_preview_list():
    preview_files_listbox.delete(0, tk.END)
    folder_path = directory_entry.get()
    extension = ext_entry.get()
    rename_type = rename_var.get()
    
    if excel_var.get():
        excel_path = excel_entry.get()
        if not excel_path:
            return
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {e}")
            return
        
        for file in os.listdir(folder_path):
            if file.endswith(extension):
                file_name, file_ext = os.path.splitext(file)
                new_name = file_name
                if rename_type == "Add/Remove":
                    new_name = file_name + df['B'].iloc[0] if df['B'].iloc[0] else file_name.replace(df['A'].iloc[0], "")
                elif rename_type == "Replace":
                    new_name = file_name.replace(df['A'].iloc[0], df['C'].iloc[0])
                new_name += file_ext
                preview_files_listbox.insert(tk.END, new_name)
    else:
        add_remove_text = add_remove_entry.get()
        replace_from_text = replace_from_entry.get()
        replace_to_text = replace_to_entry.get()

        for file in os.listdir(folder_path):
            if file.endswith(extension):
                file_name, file_ext = os.path.splitext(file)
                new_name = file_name
                if rename_type == "Add/Remove":
                    new_name = file_name + add_remove_text if add_remove_text else file_name.replace(add_remove_text, "")
                elif rename_type == "Replace":
                    new_name = file_name.replace(replace_from_text, replace_to_text)
                new_name += file_ext
                preview_files_listbox.insert(tk.END, new_name)

def execute_rename():
    folder_path = directory_entry.get()
    extension = ext_entry.get()
    rename_type = rename_var.get()
    
    if excel_var.get():
        excel_path = excel_entry.get()
        if not excel_path:
            messagebox.showerror("Error", "Please select an Excel file.")
            return
        try:
            df = pd.read_excel(excel_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read Excel file: {e}")
            return

        for file in os.listdir(folder_path):
            if file.endswith(extension):
                file_name, file_ext = os.path.splitext(file)
                new_name = file_name
                if rename_type == "Add/Remove":
                    new_name = file_name + df['B'].iloc[0] if df['B'].iloc[0] else file_name.replace(df['A'].iloc[0], "")
                elif rename_type == "Replace":
                    new_name = file_name.replace(df['A'].iloc[0], df['C'].iloc[0])
                new_name += file_ext
                os.rename(os.path.join(folder_path, file), os.path.join(folder_path, new_name))
    else:
        add_remove_text = add_remove_entry.get()
        replace_from_text = replace_from_entry.get()
        replace_to_text = replace_to_entry.get()

        for file in os.listdir(folder_path):
            if file.endswith(extension):
                file_name, file_ext = os.path.splitext(file)
                new_name = file_name
                if rename_type == "Add/Remove":
                    new_name = file_name + add_remove_text if add_remove_text else file_name.replace(add_remove_text, "")
                elif rename_type == "Replace":
                    new_name = file_name.replace(replace_from_text, replace_to_text)
                new_name += file_ext
                os.rename(os.path.join(folder_path, file), os.path.join(folder_path, new_name))
    
    messagebox.showinfo("Success", "Files renamed successfully.")
    list_files()
