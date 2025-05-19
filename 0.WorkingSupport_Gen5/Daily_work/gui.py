import tkinter as tk
from tkinter import ttk
from file_ops import*
from Handle_file import*
from compare import *

class CustomApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Customizable Application")
        self.geometry("1000x700")
        self.configure(bg="#4786E6")
        init_app_state(self)


        # PanedWindow cho phép resize các vùng
        self.paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg="#4786E6")
        self.paned.pack(fill="both", expand=True)

        # Sidebar
        self.sidebar = tk.Frame(self.paned, bg="#077786", width=200)
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="Configuration", bg="#077786", fg="white", font=("Segoe UI", 12, "bold")).pack(pady=5)
        

        # Group 1: Quản lý Excel
        frame_excel = tk.LabelFrame(self.sidebar, text="Excel mannagment", bg="#077786", fg="white")
        frame_excel.pack(fill="x", padx=8, pady=4)
        ttk.Button(frame_excel, text="Open new Excel file", command=lambda: load_excel_table(self)).pack(fill="x", pady=2)
        ttk.Button(frame_excel, text="Save Excel file", command=lambda: save_excel_table(self)).pack(fill="x", pady=2)
        ttk.Button(frame_excel, text="Open Excel file", command=lambda: open_excel_file(self)).pack(fill="x", pady=2)

        # Group 2: Chỉnh sửa bảng
        frame_edit = tk.LabelFrame(self.sidebar, text="Table setting", bg="#077786", fg="white")
        frame_edit.pack(fill="x", padx=8, pady=4)
        ttk.Button(frame_edit, text="Add column", command=lambda: add_column_to_table(self)).pack(fill="x", pady=2)
        ttk.Button(frame_edit, text="Add row", command=lambda: add_row_to_table(self)).pack(fill="x", pady=2)

        # Group 3: Quản lý workspace
        frame_ws = tk.LabelFrame(self.sidebar, text="Workspace", bg="#077786", fg="white")
        frame_ws.pack(fill="x", padx=8, pady=4)
        ttk.Button(frame_ws, text="Open new workspace", command=lambda: load_workspace(self)).pack(fill="x", pady=2)
        ttk.Button(frame_ws, text="Save workspace", command=lambda: save_workspace(self)).pack(fill="x", pady=2)
        ttk.Button(frame_ws, text="Save as workspace", command=lambda: save_workspace(self, save_as=True)).pack(fill="x", pady=2)

        # Group 4: Checking file
        frame_other = tk.LabelFrame(self.sidebar, text="Checking file", bg="#077786", fg="white")
        frame_other.pack(fill="x", padx=8, pady=4)
        self.btn_open_script = ttk.Button(frame_other, text="Open Automation script", command=lambda: open_script(self))
        self.btn_open_script.pack(fill="x", pady=2)
        ttk.Button(frame_other, text="Consistency Spec vs Script", command=lambda: compare_content_requirement(self)).pack(fill="x", pady=2)
        ttk.Button(frame_other, text="Consistency SSRS vs Spec", command=lambda: compare_ssrs_vs_spec(self)).pack(fill="x", pady=2)

        # Nút dưới cùng
        frame_refresh = tk.Frame(self.sidebar, bg="#077786")
        frame_refresh.pack(side="bottom", fill="x", padx=8, pady=8)
        ttk.Button(frame_refresh, text="Save & refresh all", command=lambda: refresh_all(self)).pack(fill="x", pady=2)

        self.paned.add(self.sidebar, minsize=120)

        # Main area
        self.main_area = tk.Frame(self.paned, bg="white")
        self.paned.add(self.main_area, minsize=300)
        tk.Label(self.main_area, text="Main Area", bg="white", font=("Segoe UI", 14, "bold")).pack(pady=10)

        # Footer
        self.footer = tk.Frame(self, bg="#e0e0e0", height=20)
        self.footer.pack(side="bottom", fill="x")
        tk.Label(self.footer, text="Develop by Nguyen Loc", bg="#e0e0e0").pack(pady=1)
        self.status_label = tk.Label(self.footer, text="", bg="#e0e0e0", fg="green", anchor="e", font=("Segoe UI", 10, "bold"))
        self.status_label.pack(side="right", padx=10)

        # Style
        style = ttk.Style()
        style.configure("Success.TButton", foreground="Green", background="#11e61b")
        style.map("Success.TButton",
          background=[('active', '#388e3c'), ('!active', '#2e7d32')])
        


        # Bind double click
        self.tree = None

        # Frame chứa Project và Test level ở dưới bên phải
        bottom_right_frame = tk.Frame(self, bg="#e0e0e0")
        bottom_right_frame.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=0)

        tk.Label(bottom_right_frame, text="Project:", bg="#e0e0e0").grid(row=0, column=0, sticky="e", padx=2)
        self.project_var = tk.StringVar(value=self.project)
        tk.Entry(bottom_right_frame, textvariable=self.project_var, width=18).grid(row=0, column=1, padx=2)

        tk.Label(bottom_right_frame, text="Test level:", bg="#e0e0e0").grid(row=1, column=0, sticky="e", padx=2)
        self.testlevel_var = tk.StringVar(value=self.Test_level)
        tk.Entry(bottom_right_frame, textvariable=self.testlevel_var, width=18).grid(row=1, column=1, padx=2)

        # --- Đồng bộ giá trị khi thay đổi ---
        def update_project_var(*args):
            self.project = self.project_var.get()
        def update_testlevel_var(*args):
            self.Test_level = self.testlevel_var.get()
        self.project_var.trace_add("write", update_project_var)
        self.testlevel_var.trace_add("write", update_testlevel_var)



