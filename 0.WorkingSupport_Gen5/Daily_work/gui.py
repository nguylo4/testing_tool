from ttkbootstrap import Style
from ttkbootstrap.constants import *
from ttkbootstrap.widgets import Frame
import ttkbootstrap as ttk
import tkinter as tk
from tkinter import filedialog, messagebox
from file_ops import *
from Handle_file import *
from compare import *
from script_handle import *
import os
import ttkbootstrap as ttk

class CollapsibleFrame(ttk.Frame):
    def __init__(self, parent, text="", width=110, *args, **kwargs):
        super().__init__(parent, width=width, *args, **kwargs)
        self.show = tk.BooleanVar(value=True)  # xổ ra mặc định
        self.text = text

        self.header = ttk.Button(
            self,
            text="- " + text,  # xổ ra mặc định là dấu -
            style="Collapsible.TButton",
            command=self.toggle,
            bootstyle="link"
        )
        self.header.pack(fill=None, anchor="w", padx=0, pady=(0, 2))

        self.sub_frame = ttk.Frame(self, style="TFrame", width=width)
        self.sub_frame.pack(side="left", fill=None, expand=False)  # pack luôn khi khởi tạo

    def toggle(self):
        if self.show.get():
            self.sub_frame.forget()
            self.header.config(text="+ " + self.text)
        else:
            self.sub_frame.pack(side="left", fill=None, expand=False)
            self.header.config(text="- " + self.text)
        self.show.set(not self.show.get())



class CustomApp(ttk.Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        style = Style()
        self.title("Release working")
        self.geometry("1000x700")

        # Style definitions
        style.configure("Sidebar.TFrame", background="#FFFFFF")
        style.configure("Sidebar.TLabel", font=("Segoe UI", 12, "bold"), background="#ffffff")
        style.configure("Custom.TLabelframe", background="#ffffff", relief="flat")
        style.configure("Custom.TLabelframe.Label", font=("Segoe UI", 10, "bold"), background="#ffffff", foreground="#333")
        style.configure("TButton", font=("Segoe UI", 8), padding=2)
        style.configure("Success.TButton", foreground="Green", background="#11e61b")
        style.map("Success.TButton", background=[('active', "#ffffff"), ('!active', "#ffffff")])
        style.configure("StatusSuccess.TLabel", foreground="green", font=("Segoe UI", 10, "bold"))
        style.configure("StatusError.TLabel", foreground="red", font=("Segoe UI", 10, "bold"))
        # Thêm style cho header button (nên đặt sau style = Style())
        style.configure("Collapsible.TButton", font=("Segoe UI", 8), foreground="#222", anchor="w", relief="flat", background="#FFFFFF")
        
        ico_path = os.path.join(os.path.dirname(__file__), "App.ico")
        self.iconbitmap(ico_path)
        
        init_app_state(self)

        self._workspace_to_load = None

        # Startup popup
        self.withdraw()

        def on_load_workspace():
            file_path = filedialog.askopenfilename(title="Open workspace", filetypes=[("JSON files", "*.json")])
            if file_path:
                self._workspace_to_load = file_path
                self.project = project_var.get()
                self.Test_level = testlevel_var.get()
                popup.destroy()
            else:
                messagebox.showinfo("Noted!", "Not any workspace loaded!")

        def on_ok():
            self.project = project_var.get()
            self.Test_level = testlevel_var.get()
            popup.destroy()

        popup = tk.Toplevel(self)
        popup.title("Selection Project and Test level")
        popup.geometry("320x190")
        popup.iconbitmap(ico_path)
        popup.grab_set()
        popup.resizable(False, False)

        tk.Label(popup, text="Project:", font=("Segoe UI", 11)).pack(pady=(18, 2))
        project_var = tk.StringVar(value=self.project)
        tk.Entry(popup, textvariable=project_var, width=28).pack()

        tk.Label(popup, text="Test level:", font=("Segoe UI", 11)).pack(pady=(10, 2))
        testlevel_var = tk.StringVar(value=self.Test_level)
        tk.Entry(popup, textvariable=testlevel_var, width=28).pack()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=16)
        ttk.Button(btn_frame, text="OK", width=10, command=on_ok).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="Load workspace", width=16, command=on_load_workspace).pack(side="left", padx=6)

        self.wait_window(popup)
        self.deiconify()

        # === Tabs (Notebook) chỉ để chọn sidebar chức năng ===
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(side="top", fill="x", padx=0, pady=0)

        # --- Tab File ---
        file_tab = ttk.Frame(self.notebook)
        self.notebook.add(file_tab, text="File")
        file_sidebar = ttk.Frame(file_tab, style="Sidebar.TFrame", width=2500, height=60)
        file_sidebar.pack(fill=None, expand=False, side="top", anchor="w")
        file_sidebar.pack_propagate(False)

        # Các group xếp ngang
        excel_frame = CollapsibleFrame(file_sidebar, text="📂 Excel File", width=110)
        excel_frame.pack(side="left", padx=4, pady=4, anchor="w")
        workspace_frame = CollapsibleFrame(file_sidebar, text="🧩 Workspace", width=110)
        workspace_frame.pack(side="left", padx=4, pady=4, anchor="w")

        # Các nút trong group cũng xếp ngang
        ttk.Button(excel_frame.sub_frame, text="📄 Open New", bootstyle="outline", width=21, command=lambda: load_excel_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(excel_frame.sub_frame, text="💾 Save", bootstyle="success", width=21, command=lambda: save_excel_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(excel_frame.sub_frame, text="📂 Edit", bootstyle="secondary", width=21, command=lambda: open_excel_file(self)).pack(side="left", padx=2, pady=1)

        ttk.Button(workspace_frame.sub_frame, text="🆕 Open New", bootstyle="outline", width=21, command=lambda: load_workspace(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(workspace_frame.sub_frame, text="💾 Save", bootstyle="success", width=21, command=lambda: save_workspace(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(workspace_frame.sub_frame, text="📁 Save As", bootstyle="secondary", width=21, command=lambda: save_workspace(self, save_as=True)).pack(side="left", padx=2, pady=1)

        # --- Tab Working ---
        working_tab = ttk.Frame(self.notebook)
        self.notebook.add(working_tab, text="Working")
        working_sidebar = ttk.Frame(working_tab, style="Sidebar.TFrame", width=2500, height=60)
        working_sidebar.pack(fill=None, expand=False, side="top", anchor="w")
        working_sidebar.pack_propagate(False)

        # Các group xếp ngang
        table_frame = CollapsibleFrame(working_sidebar, text="📋 Table Settings", width=110)
        table_frame.pack(side="left", padx=4, pady=4, anchor="w")
        consistency_frame = CollapsibleFrame(working_sidebar, text="🔍 Consistency", width=110)
        consistency_frame.pack(side="left", padx=4, pady=4, anchor="w")
        script_frame = CollapsibleFrame(working_sidebar, text="📜 Scripting", width=110)
        script_frame.pack(side="left", padx=4, pady=4, anchor="w")

        # Các nút trong group cũng xếp ngang
        ttk.Button(table_frame.sub_frame, text="➕ Add Column", bootstyle="primary", width=21, command=lambda: add_column_to_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(table_frame.sub_frame, text="➕ Add Row", bootstyle="primary", width=21, command=lambda: add_row_to_table(self)).pack(side="left", padx=2, pady=1)

        ttk.Button(consistency_frame.sub_frame, text="🔍 SPEC vs Script", bootstyle="warning", width=21, command=lambda: compare_content_requirement(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(consistency_frame.sub_frame, text="🔎 SSRS vs SPEC", bootstyle="warning", width=21, command=lambda: compare_ssrs_vs_spec(self)).pack(side="left", padx=2, pady=1)

        ttk.Button(script_frame.sub_frame, text="📂 Open", bootstyle="outline", width=21, command=lambda: open_script(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(script_frame.sub_frame, text="🛠️ Create", bootstyle="info", width=21, command=lambda: create_new_script(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(script_frame.sub_frame, text="⬇️ Download", bootstyle="secondary", width=21, command=lambda: download_script(self)).pack(side="left", padx=2, pady=1)


        # --- Tab About ---
        about_tab = ttk.Frame(self.notebook)
        self.notebook.add(about_tab, text="About")

        def show_about_popup():
            popup = tk.Toplevel(self)
            popup.title("About")
            popup.geometry("340x200")
            popup.iconbitmap(ico_path)
            popup.resizable(False, False)
            ttk.Label(popup, text="Release Working Tool\nVersion 1.1\nDeveloped by NguyenLoc", font=("Segoe UI", 13, "bold")).pack(pady=30)
            ttk.Label(popup, text="Contact: loc.nguyen@forvia.com", font=("Segoe UI", 10)).pack(pady=5)
            ttk.Button(popup, text="Close", command=popup.destroy, bootstyle="danger").pack(pady=18)
            popup.grab_set()
        def on_tab_changed(event):
            if self.notebook.index("current") == 2:  # About tab index
                show_about_popup()
                self.notebook.select(0)  # Quay lại tab đầu tiên sau khi đóng popup
        self.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

        # === Main Area luôn hiển thị bên phải ===
        self.main_area = ttk.Frame(self, style="TFrame")
        self.main_area.pack(side="top", fill="both", expand=True)
        ttk.Label(self.main_area, text="Main Area", style="TLabel", font=("Segoe UI", 14, "bold")).pack(pady=10)
        self.status_label = ttk.Label(self, text="", style="StatusSuccess.TLabel", anchor="e", font=("Segoe UI", 10, "bold"))
        self.status_label.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

        # --- Footer -------------------------------------------------------------------------------------------------------------------
        self.footer = ttk.Frame(self, style="TFrame", height=20)
        self.footer.pack(side="bottom", fill="x")
        # ttk.Label(self.footer, text="Develop by NguyenLoc", style="TLabel").pack(pady=1)
        self.save_button = ttk.Button(
            self.footer,
            text="✅ Save & Refresh All",
            bootstyle="success",
            width=27,
            command=lambda: refresh_all(self)
        )
        self.save_button.pack(side="left", padx=200, pady=8)
        # self.save_button = ttk.Label(self.footer, text="", style="TLabel", foreground="green", anchor="e", font=("Segoe UI", 10, "bold"))
        self.status_label.place(relx=0.0, rely=1.0, anchor="sw", x=100, y=-10)

        self.tree = None

        bottom_left_frame = ttk.Frame(self, style="TFrame")
        bottom_left_frame.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=-10)
        ttk.Label(bottom_left_frame, text="Project:", style="TLabel").grid(row=0, column=0, sticky="e", padx=2)
        self.project_var = tk.StringVar(value=self.project)
        ttk.Entry(bottom_left_frame, textvariable=self.project_var, width=15).grid(row=0, column=1, padx=2)
        ttk.Label(bottom_left_frame, text="Test level:", style="TLabel").grid(row=1, column=0, sticky="e", padx=2)
        self.testlevel_var = tk.StringVar(value=self.Test_level)
        ttk.Entry(bottom_left_frame, textvariable=self.testlevel_var, width=15).grid(row=1, column=1, padx=2)

        def update_project_var(*args):
            self.project = self.project_var.get()
        def update_testlevel_var(*args):
            self.Test_level = self.testlevel_var.get()

        self.project_var.trace_add("write", update_project_var)
        self.testlevel_var.trace_add("write", update_testlevel_var)

        if self._workspace_to_load:
            load_workspace(self, file_path=self._workspace_to_load)

        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=250, mode="determinate", maximum=20, variable=self.progress_var, bootstyle="success-striped")
        self.progress_bar.place(relx=0.5, rely=1.0, anchor="s", y=-5)
        self.progress_bar.lower()

        self.file_sidebar = file_sidebar
        self.working_sidebar = working_sidebar




