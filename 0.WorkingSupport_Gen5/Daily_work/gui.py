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
        style.configure("TButton", font=("Segoe UI", 10), padding=4)
        style.configure("Success.TButton", foreground="Green", background="#11e61b")
        style.map("Success.TButton", background=[('active', "#ffffff"), ('!active', "#ffffff")])
        style.configure("StatusSuccess.TLabel", foreground="green", font=("Segoe UI", 10, "bold"))
        style.configure("StatusError.TLabel", foreground="red", font=("Segoe UI", 10, "bold"))

        
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

        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg="#f0f4f7")
        self.paned.pack(fill="both", expand=True)

        self.sidebar = ttk.Frame(self.paned, style="Sidebar.TFrame", width=220)
        self.sidebar.pack_propagate(False)
        ttk.Label(self.sidebar, text="Configuration", style="Sidebar.TLabel").pack(pady=8)

       # === Excel Management ===
        excel_frame = ttk.Labelframe(self.sidebar, text="📂 Excel Management")
        excel_frame.pack(fill="x", padx=12, pady=6, ipadx=4, ipady=4)

        ttk.Button(excel_frame, text="📄 Open New Excel File", bootstyle="outline", command=lambda: load_excel_table(self)).pack(fill=X, pady=2)
        ttk.Button(excel_frame, text="💾 Save Excel File", bootstyle="success", command=lambda: save_excel_table(self)).pack(fill=X, pady=2)
        ttk.Button(excel_frame, text="📂 Edit in Excel", bootstyle="secondary", command=lambda: open_excel_file(self)).pack(fill=X, pady=2)

        # === Workspace ===
        workspace_frame = ttk.Labelframe(self.sidebar, text="🧩 Workspace", padding=10)
        workspace_frame.pack(padx=10, pady=5, fill=X)

        ttk.Button(workspace_frame, text="🆕 Open New Workspace", bootstyle="outline", command=lambda: load_workspace(self)).pack(fill=X, pady=2)
        ttk.Button(workspace_frame, text="💾 Save Workspace", bootstyle="success", command=lambda: save_workspace(self)).pack(fill=X, pady=2)
        ttk.Button(workspace_frame, text="📁 Save As Workspace", bootstyle="secondary", command=lambda: save_workspace(self, save_as=True)).pack(fill=X, pady=2)

        # === Table Setting ===
        table_frame = ttk.Labelframe(self.sidebar, text="📋 Table Settings", padding=10)
        table_frame.pack(padx=10, pady=5, fill=X)

        ttk.Button(table_frame, text="➕ Add Column", bootstyle="primary", command=lambda: add_column_to_table(self)).pack(fill=X, pady=2)
        ttk.Button(table_frame, text="➕ Add Row", bootstyle="primary", command=lambda: add_row_to_table(self)).pack(fill=X, pady=2)

        # === Consistency Check ===
        consistency_frame = ttk.Labelframe(self.sidebar, text="🔍 Consistency Check", padding=10)
        consistency_frame.pack(padx=10, pady=5, fill=X)

        ttk.Button(consistency_frame, text="🔍 SPEC vs Script", bootstyle="warning", command=lambda: compare_content_requirement(self)).pack(fill=X, pady=2)
        ttk.Button(consistency_frame, text="🔎 SSRS vs SPEC", bootstyle="warning", command=lambda: compare_ssrs_vs_spec(self)).pack(fill=X, pady=2)

        # === Scripting ===
        script_frame = ttk.Labelframe(self.sidebar, text="📜 Scripting", padding=10)
        script_frame.pack(padx=10, pady=5, fill=X)

        ttk.Button(script_frame, text="📂 Open Script", bootstyle="outline", command=lambda: open_script(self)).pack(fill=X, pady=2)
        ttk.Button(script_frame, text="🛠️ Create Script", bootstyle="info", command=lambda: create_new_script(self)).pack(fill=X, pady=2)
        ttk.Button(script_frame, text="⬇️ Download Script", bootstyle="secondary", command=lambda: download_script(self)).pack(fill=X, pady=2)

        # === Save All ===
        ttk.Button(self.sidebar, text="✅ Save & Refresh All", bootstyle="success", command=lambda: refresh_all(self)).pack(pady=10, fill=X)

        self.paned.add(self.sidebar, minsize=120)

        self.main_area = ttk.Frame(self.paned, style="TFrame")
        self.paned.add(self.main_area, minsize=300)
        ttk.Label(self.main_area, text="Main Area", style="TLabel", font=("Segoe UI", 14, "bold")).pack(pady=10)

        self.footer = ttk.Frame(self, style="TFrame", height=20)
        self.footer.pack(side="bottom", fill="x")
        ttk.Label(self.footer, text="Develop by NguyenLoc", style="TLabel").pack(pady=1)
        self.status_label = ttk.Label(self.footer, text="", style="TLabel", foreground="green", anchor="e", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="right", padx=10)

        self.tree = None

        bottom_left_frame = ttk.Frame(self, style="TFrame")
        bottom_left_frame.place(relx=0.0, rely=1.0, anchor="sw", x=10, y=0)
        ttk.Label(bottom_left_frame, text="Project:", style="TLabel").grid(row=0, column=0, sticky="e", padx=2)
        self.project_var = tk.StringVar(value=self.project)
        ttk.Entry(bottom_left_frame, textvariable=self.project_var, width=18).grid(row=0, column=1, padx=2)
        ttk.Label(bottom_left_frame, text="Test level:", style="TLabel").grid(row=1, column=0, sticky="e", padx=2)
        self.testlevel_var = tk.StringVar(value=self.Test_level)
        ttk.Entry(bottom_left_frame, textvariable=self.testlevel_var, width=18).grid(row=1, column=1, padx=2)

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




