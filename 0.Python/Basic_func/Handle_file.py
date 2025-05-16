import os
import shutil
import stat
from tkinter import messagebox
import subprocess
from openpyxl import load_workbook

def copy_file_by_name(input_folder, output_folder, filename):
    """
    Copy a file with the given filename from input_folder to output_folder.
    After copying, make sure the file is writable.
    Return (success: bool, input_path: str)
    """
    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename)
    try:
        if not os.path.exists(input_path):
            return False, input_path
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        shutil.copy2(input_path, output_path)
        os.chmod(output_path, stat.S_IWRITE | stat.S_IREAD)
        print(f"Copied '{input_path}' to '{output_path}' and made it writable")
        return True, input_path
    except Exception as e:
        print(f"Error: {e}")
        return False, input_path

def open_file(filepath):
    try:
        os.startfile(filepath)  # Chỉ dùng được trên Windows
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file: {e}")

def open_excel_file(input_folder, file_name):
    input_path = os.path.join(input_folder, file_name)
    try:
        if not os.path.exists(input_path):
            return False
        # Mở file Excel bằng subprocess
        subprocess.Popen(['start', 'excel', input_path], shell=True)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False, input_path

def write_excel_cell_by_label(filepath, row_label, col_label, value, sheet_name=None):
    """
    Ghi giá trị vào file Excel tại vị trí xác định bởi (row_label, col_label).
    row_label: giá trị ở cột đầu tiên (ví dụ: tên hàng)
    col_label: giá trị ở hàng đầu tiên (ví dụ: tên cột)
    """
    wb = load_workbook(filepath)
    ws = wb[sheet_name] if sheet_name else wb.active

    # Tìm vị trí cột theo col_label (ở hàng 1)
    col_idx = None
    for cell in ws[1]:
        if cell.value == col_label:
            col_idx = cell.column
            break
    if col_idx is None:
        raise ValueError(f"Không tìm thấy cột '{col_label}'")

    # Tìm vị trí hàng theo row_label (ở cột A)
    row_idx = None
    for row in ws.iter_rows(min_row=2, max_col=1):
        if row[0].value == row_label:
            row_idx = row[0].row
            break
    if row_idx is None:
        raise ValueError(f"Không tìm thấy hàng '{row_label}'")

    # Ghi giá trị vào ô xác định
    ws.cell(row=row_idx, column=col_idx, value=value)
    wb.save(filepath)
    wb.close()

def read_excel_cell_by_label(filepath, row_label, col_label, sheet_name=None):
    """
    Đọc giá trị trong file Excel tại vị trí xác định bởi (row_label, col_label).
    row_label: giá trị ở cột đầu tiên (ví dụ: tên hàng)
    col_label: giá trị ở hàng đầu tiên (ví dụ: tên cột)
    """
    wb = load_workbook(filepath)
    ws = wb[sheet_name] if sheet_name else wb.active

    # Tìm vị trí cột theo col_label (ở hàng 1)
    col_idx = None
    for cell in ws[1]:
        if cell.value == col_label:
            col_idx = cell.column
            break
    if col_idx is None:
        wb.close()
        raise ValueError(f"Không tìm thấy cột '{col_label}'")

    # Tìm vị trí hàng theo row_label (ở cột A)
    row_idx = None
    for row in ws.iter_rows(min_row=2, max_col=1):
        if row[0].value == row_label:
            row_idx = row[0].row
            break
    if row_idx is None:
        wb.close()
        raise ValueError(f"Không tìm thấy hàng '{row_label}'")
    
    # Đọc giá trị tại ô xác định
    value = ws.cell(row=row_idx, column=col_idx).value
    wb.close()
    return value
    
