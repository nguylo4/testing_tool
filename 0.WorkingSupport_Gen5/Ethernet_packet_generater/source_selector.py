import os
from PyQt5.QtWidgets import QFileDialog, QInputDialog

class SourceSelector:
    def __init__(self):
        self.source_folder = ""
        self.variants = []
        self.selected_variant = ""

    def select_source_folder(self, parent_widget):
        # Đặt thư mục mặc định là Y:/Source nếu tồn tại
        default_dir = "Y:/Source"
        if not os.path.isdir(default_dir):
            default_dir = ""
        folder_path = QFileDialog.getExistingDirectory(parent_widget, "Chọn thư mục Source Autosar", default_dir)
        if not folder_path:
            raise FileNotFoundError("Chưa chọn thư mục.")
        self.source_folder = folder_path
        base_path = os.path.join(folder_path, "Autosar")
        if not os.path.isdir(base_path):
            raise FileNotFoundError("Không tìm thấy thư mục Autosar trong thư mục đã chọn.")
        self.variants = [f for f in os.listdir(base_path)
                         if os.path.isdir(os.path.join(base_path, f))]
        if not self.variants:
            raise FileNotFoundError("Không có variant nào trong Autosar.")
        return self.variants

    def choose_variant(self, parent_widget):
        if not self.variants:
            raise RuntimeError("Chưa load danh sách variant, hãy gọi select_source_folder() trước.")
        variant, ok = QInputDialog.getItem(parent_widget, "Chọn variant", "Chọn variant:", self.variants, 0, False)
        if not ok or not variant:
            raise ValueError("Bạn chưa chọn variant.")
        self.selected_variant = variant
        return self.selected_variant
