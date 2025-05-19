import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
import os
import re

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

if __name__ == "__main__":
    app = HTMLMergerApp()
    app.mainloop()