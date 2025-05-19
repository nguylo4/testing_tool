
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
from tkinter import ttk
import os
import re

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