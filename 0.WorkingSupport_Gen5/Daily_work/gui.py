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
from edit_report import *
from ttkbootstrap.window import Window
from tool_updater import check_update

# KANBAN_STATES = [
#     "Start", "Prepare_Spec", "Spec_Done", "Implement TC", "Executed", "Review", "Done"
# ]

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



class CustomApp(Window):
    def __init__(self):
        super().__init__(themename="cosmo")
        style = Style()
        self.title("Testing Tool")
        self.geometry("1200x900")

        # Style definitions
        style.configure("Sidebar.TFrame", background="#ffffff")
        style.configure("Sidebar.TLabel", font=("Segoe UI", 12, "bold"), background="#ffffff")
        style.configure("Custom.TLabelframe", background="#ffffff", relief="flat")
        style.configure("Custom.TLabelframe.Label", font=("Segoe UI", 10, "bold"), background="#ffffff", foreground="#333")
        style.configure("TButton", font=("Segoe UI", 8), padding=2)
        style.configure("Success.TButton", foreground="Green", background="#11e61b")
        style.map("Success.TButton", background=[('active', "#ffffff"), ('!active', "#ffffff")])
        style.configure("StatusSuccess.TLabel", foreground="green", font=("Segoe UI", 10, "bold"))
        style.configure("StatusError.TLabel", foreground="red", font=("Segoe UI", 10, "bold"))
        # Thêm style cho header button (nên đặt sau style = Style())
        style.configure("Bold.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Collapsible.TButton", font=("Segoe UI", 8, "bold"), foreground="#222", anchor="w", relief="flat", background="#ffffff")
        
        ico_path = os.path.join(os.path.dirname(__file__), "App.ico")
        self.iconbitmap(ico_path)
        
        init_app_state(self)
        self.sheet = None
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
        table_frame = CollapsibleFrame(file_sidebar, text="📋 Table Settings", width=110)
        table_frame.pack(side="left", padx=4, pady=4, anchor="w")

        # Các nút trong group cũng xếp ngang
        ttk.Button(excel_frame.sub_frame, text="📄 Open New", bootstyle="outline", width=21, command=lambda: load_excel_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(excel_frame.sub_frame, text="💾 Save", bootstyle="success", width=21, command=lambda: save_excel_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(excel_frame.sub_frame, text="📂 Edit", bootstyle="secondary", width=21, command=lambda: open_excel_file(self)).pack(side="left", padx=2, pady=1)

        ttk.Button(workspace_frame.sub_frame, text="🆕 Open New", bootstyle="outline", width=21, command=lambda: load_workspace(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(workspace_frame.sub_frame, text="💾 Save", bootstyle="success", width=21, command=lambda: save_workspace(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(workspace_frame.sub_frame, text="📁 Save As", bootstyle="secondary", width=21, command=lambda: save_workspace(self, save_as=True)).pack(side="left", padx=2, pady=1)

        ttk.Button(table_frame.sub_frame, text="➕ Add Column", bootstyle="primary", width=21, command=lambda: add_column_to_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(table_frame.sub_frame, text="➕ Add Row", bootstyle="primary", width=21, command=lambda: add_row_to_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(table_frame.sub_frame, text="➖ Delete Column", bootstyle="danger", width=21, command=lambda: delete_column_from_table(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(table_frame.sub_frame, text="➖ Delete Row", bootstyle="danger", width=21, command=lambda: delete_row_from_table(self)).pack(side="left", padx=2, pady=1)

        # --- Tab Working ---
        working_tab = ttk.Frame(self.notebook)
        self.notebook.add(working_tab, text="Working")
        working_sidebar = ttk.Frame(working_tab, style="Sidebar.TFrame", width=2500, height=60)
        working_sidebar.pack(fill=None, expand=False, side="top", anchor="w")
        working_sidebar.pack_propagate(False)

        # Các group xếp ngang
        
        consistency_frame = CollapsibleFrame(working_sidebar, text="🔍 Consistency", width=110)
        consistency_frame.pack(side="left", padx=4, pady=4, anchor="w")
        script_frame = CollapsibleFrame(working_sidebar, text="📜 Scripting", width=110)
        script_frame.pack(side="left", padx=4, pady=4, anchor="w")
        

        # Các nút trong group cũng xếp ngang
        ttk.Button(consistency_frame.sub_frame, text="🔍 SPEC vs Script", bootstyle="warning", width=21, command=lambda: compare_content_requirement(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(consistency_frame.sub_frame, text="🔎 SSRS vs SPEC", bootstyle="warning", width=21, command=lambda: compare_ssrs_vs_spec(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(consistency_frame.sub_frame, text="🧮 Compare Attribute", bootstyle="info", width=21, command=lambda: compare_attribute(self)).pack(side="left", padx=2, pady=1)

        ttk.Button(script_frame.sub_frame, text="📂 Open", bootstyle="outline", width=21, command=lambda: open_script(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(script_frame.sub_frame, text="🛠️ Create", bootstyle="info", width=21, command=lambda: create_new_script(self)).pack(side="left", padx=2, pady=1)
        ttk.Button(script_frame.sub_frame, text="⬇️ Download", bootstyle="secondary", width=21, command=lambda: download_script(self)).pack(side="left", padx=2, pady=1)
        
        
        # --- Tab About ---
        about_tab = ttk.Frame(self.notebook)
        self.notebook.add(about_tab, text="About")

        def show_about_popup():
            popup = tk.Toplevel(self)
            popup.title("About")
            popup.geometry("300x270")
            popup.iconbitmap(ico_path)
            popup.resizable(False, False)
            ttk.Label(popup, text="Release Working Tool\nVersion 1.2\nDeveloped by NguyenLoc", font=("Segoe UI", 13, "bold")).pack(pady=20)
            ttk.Label(popup, text="Contact: loc.nguyen@forvia.com", font=("Segoe UI", 10)).pack(pady=5)
            
            def on_check_update():
                result = check_update()
                messagebox.showinfo("Kiểm tra cập nhật", result, parent=popup)
            
            ttk.Button(popup, text="Kiểm tra cập nhật", command=on_check_update, bootstyle="info").pack(pady=4)
            ttk.Button(popup, text="Close", command=popup.destroy, bootstyle="danger").pack(pady=8)
            popup.grab_set()
        def on_tab_changed(event):
            if self.notebook.index("current") == 2:  # About tab index
                show_about_popup()
                self.notebook.select(0)  # Quay lại tab đầu tiên sau khi đóng popup
        self.notebook.bind("<<NotebookTabChanged>>", on_tab_changed)

        # --- Tab Kanban ---
        # from tkinter import ttk as tkttk  # Đảm bảo import này ở đầu file nếu chưa có
        # kanban_tab = ttk.Frame(self.notebook)
        # self.notebook.add(kanban_tab, text="Kanban")
        # self.kanban_view = KanbanView(kanban_tab, self)
        # self.kanban_view.pack(fill="both", expand=True)

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



# class KanbanView(ttk.Frame):
#     def __init__(self, parent, app):
#         super().__init__(parent)
#         self.app = app
#         self.lists = {}
#         self.frames = {}
#         for i, state in enumerate(KANBAN_STATES):
#             frame = ttk.Labelframe(self, text=state, width=220, height=500, style="Custom.TLabelframe")
#             frame.grid(row=0, column=i, padx=8, pady=8, sticky="n")
#             frame.grid_propagate(False)
#             self.frames[state] = frame
#             lb = tk.Listbox(frame, width=20, height=22, font=("Segoe UI", 10, "bold"))
#             lb.pack(fill="both", expand=True, padx=4, pady=4)
#             lb.bind("<ButtonPress-1>", self.on_drag_start)
#             lb.bind("<B1-Motion>", self.on_drag_motion)
#             lb.bind("<ButtonRelease-1>", self.on_drag_release)
#             self.lists[state] = lb

#         self.drag_data = {"widget": None, "item": None, "from_state": None}

#         self.refresh_kanban()

#     def refresh_kanban(self):
#         # Xóa hết các list
#         for lb in self.lists.values():
#             lb.delete(0, "end")
#         # Lấy index các cột
#         try:
#             tc_idx = self.app.headers.index("Test cases ID")
#             req_idx = self.app.headers.index("Requirement ID")
#             cr_idx = self.app.headers.index("CR ID")
#             state_idx = self.app.headers.index("State")
#         except Exception:
#             return
#         # Thêm từng testcase vào đúng state
#         for row in self.app.data:
#             state = row[state_idx] if state_idx < len(row) else "Start"
#             state = state if state in KANBAN_STATES else "Start"
#             tcid = str(row[tc_idx])
#             reqid = str(row[req_idx]) if req_idx is not None else ""
#             crid = str(row[cr_idx]) if cr_idx is not None else ""
#             display = f"{tcid}\nReq: {reqid}\nCR: {crid}"
#             self.lists[state].insert("end", display)

#     def on_drag_start(self, event):
#         widget = event.widget
#         idx = widget.nearest(event.y)
#         if idx >= 0:
#             self.drag_data["widget"] = widget
#             self.drag_data["item"] = widget.get(idx)
#             self.drag_data["from_state"] = self.get_state_by_widget(widget)
#             widget.selection_set(idx)

#     def on_drag_motion(self, event):
#         pass  # Optional: highlight target column

#     def on_drag_release(self, event):
#         widget = event.widget
#         if self.drag_data["item"]:
#             # Xác định state mới
#             for state, lb in self.lists.items():
#                 if lb == widget:
#                     new_state = state
#                     break
#             else:
#                 return
#             # Xóa khỏi state cũ
#             from_lb = self.lists[self.drag_data["from_state"]]
#             idx = from_lb.get(0, "end").index(self.drag_data["item"])
#             from_lb.delete(idx)
#             # Thêm vào state mới
#             widget.insert("end", self.drag_data["item"])
#             # Cập nhật state trong bảng
#             self.update_table_state(self.drag_data["item"].split("\n")[0], new_state)
#             self.drag_data = {"widget": None, "item": None, "from_state": None}

#     def get_state_by_widget(self, widget):
#         for state, lb in self.lists.items():
#             if lb == widget:
#                 return state
#         return None

#     def update_table_state(self, tcid, new_state):
#         try:
#             tc_idx = self.app.headers.index("Test cases ID")
#             state_idx = self.app.headers.index("State")
#         except Exception:
#             return
#         for row in self.app.data:
#             if str(row[tc_idx]) == tcid:
#                 row[state_idx] = new_state
#         refresh_table(self.app)

# def add_row_to_table(app):
#     from file_ops import refresh_table
#     if not app.excel_path:
#         messagebox.showwarning("Error", "Open excel file before!")
#         return
#     new_row = [""] * len(app.headers)
#     # Đảm bảo có cột State
#     if "State" in app.headers:
#         state_idx = app.headers.index("State")
#         new_row[state_idx] = "Start"
#     app.data.append(new_row)
#     refresh_table(app)
#     if hasattr(app, "kanban_view"):
#         app.kanban_view.refresh_kanban()






