import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QHBoxLayout, QMessageBox, QTextEdit
)
from PyQt5.QtGui import QIcon
import pandas as pd
from dbc_utils import parse_csv, get_messages, get_signals, calc_signal_raw, build_payload
from eth_packet import EthernetPacketBuilder, send_udp_packet
from autosar_utils import get_eth_info
from source_selector import SourceSelector
from packet_detail_widget import PacketDetailWidget  # Import widget mới
from Create_CAPL_node import create_capl_node

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DBC", "DBC.csv")

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ethernet Packet Generator")
        if getattr(sys, 'frozen', False):
            # Đang chạy trong exe
            ico_path = os.path.join(sys._MEIPASS, 'icon/App.ico')
        else:
            # Đang chạy file .py
            ico_path = os.path.join(os.path.dirname(__file__), "icon/App.ico")

        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), ico_path)))  # Thêm dòng này
        self.resize(900, 600)
        self.df = parse_csv(CSV_PATH)
        self.init_ui()
        self.source_selector = SourceSelector()
        self.autosar_root = ""
        self.base_system = ""
        self.variant = ""

    def init_ui(self):
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()

        # Thanh search và chọn message + kiểu nhập value trên cùng 1 hàng
        top_row = QHBoxLayout()
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Tìm Message...")
        self.search_edit.setFixedWidth(140)
        self.search_edit.setFixedHeight(30)
        self.search_edit.textChanged.connect(self.filter_messages)
        top_row.addWidget(self.search_edit)

        self.msg_combo = QComboBox()
        self.msg_combo.setMinimumWidth(220)
        self.msg_combo.setFixedHeight(30)
        self.msg_combo.setEditable(True)
        self.all_messages = get_messages(self.df)
        self.msg_combo.addItems(self.all_messages)
        self.msg_combo.currentTextChanged.connect(self.load_signals)
        self.search_edit.textChanged.connect(lambda _: self.msg_combo.showPopup())
        top_row.addWidget(self.msg_combo)

        self.value_option_combo = QComboBox()
        self.value_option_combo.setFixedWidth(100)
        self.value_option_combo.setFixedHeight(30)
        self.value_option_combo.addItems([
            "Custom", "Min", "Max", "Mid", "Min - Res", "Min + Res", "Max - Res", "Max + Res"
        ])
        self.value_option_combo.currentTextChanged.connect(self.apply_value_option)
        top_row.addWidget(self.value_option_combo)

        left_layout.addLayout(top_row)

        self.table = QTableWidget()
        left_layout.addWidget(self.table)
        main_layout.addLayout(left_layout, 2)

        # Bên phải: output và nút
        right_layout = QVBoxLayout()
        # Thay thế phần payload_label và payload_edit bằng widget mới
        self.packet_detail_widget = PacketDetailWidget()
        self.packet_detail_widget.setFixedWidth(550)
        right_layout.addWidget(self.packet_detail_widget)
        right_layout.addStretch()

        # Nút tạo ETH Packet (mới, đặt trên)
        self.eth_btn = QPushButton("Tạo ETH Packet")
        self.eth_btn.setMinimumHeight(40)
        self.eth_btn.setStyleSheet("font-size: 16px; background-color: #90ee90;")
        self.eth_btn.clicked.connect(self.create_eth_packet_auto)
        right_layout.addWidget(self.eth_btn)

        # Nút tạo CAPL node
        self.create_capl_btn = QPushButton("Tạo CAPL Node")
        self.create_capl_btn.setMinimumHeight(35)
        self.create_capl_btn.setStyleSheet("font-size: 15px; background-color: #ffe4b5;")
        self.create_capl_btn.clicked.connect(self.create_capl_node_action)
        right_layout.addWidget(self.create_capl_btn)

        # Nút tạo payload (cũ)
        # self.gen_btn = QPushButton("Tạo Payload")
        # self.gen_btn.setMinimumHeight(35)
        # self.gen_btn.setStyleSheet("font-size: 15px; background-color: #90ee90;")
        # self.gen_btn.clicked.connect(self.generate_payload)
        # right_layout.addWidget(self.gen_btn)

        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)
        self.load_signals(self.msg_combo.currentText())
        self.send_btn = QPushButton("Gửi ETH Packet")
        self.send_btn.setMinimumHeight(35)
        self.send_btn.setStyleSheet("font-size: 16px; background-color: #ffb347;")
        self.send_btn.clicked.connect(self.send_eth_packet)
        right_layout.addWidget(self.send_btn)

    def load_signals(self, message):
        self.signals, self.total_len = get_signals(self.df, message)
        self.table.setRowCount(len(self.signals))
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "Signal", "Phys Value", "Factor", "Offset", "Min", "Max", "Unit", "Start Bit", "Lenth", "Raw Value"
        ])
        for i, row in self.signals.iterrows():
            self.table.setItem(i, 0, QTableWidgetItem(row['dbc_Signal']))
            val = row['dbc_InitialValue']
            if val == '' or pd.isna(val):
                val = '0'
            le = QLineEdit(str(val))
            self.table.setCellWidget(i, 1, le)
            self.table.setItem(i, 2, QTableWidgetItem(str(row['dbc_Factor'])))
            self.table.setItem(i, 3, QTableWidgetItem(str(row['dbc_Offset'])))
            self.table.setItem(i, 4, QTableWidgetItem(str(row['dbc_Minimum'])))
            self.table.setItem(i, 5, QTableWidgetItem(str(row['dbc_Maximum'])))
            self.table.setItem(i, 6, QTableWidgetItem(str(row['dbc_Unit'])))
            self.table.setItem(i, 7, QTableWidgetItem(str(int(float(row['dbc_Startbit'])))))
            self.table.setItem(i, 8, QTableWidgetItem(str(int(float(row['dbc_Length [bit]'])))))
        # self.payload_label.setText("Payload (Hex):")  # Đã bỏ widget này, xóa dòng này
        # Reset về Custom khi đổi message
        self.value_option_combo.setCurrentText("Custom")


    def apply_value_option(self, option):
        for i, row in self.signals.iterrows():
            minv = row['dbc_Minimum']
            maxv = row['dbc_Maximum']
            factor = row['dbc_Factor']
            offset = row['dbc_Offset']
            le = self.table.cellWidget(i, 1)
            try:
                minv_f = float(minv) if minv != '' else 0
                maxv_f = float(maxv) if maxv != '' else 0
                factor_f = float(factor) if factor != '' else 1
                offset_f = float(offset) if offset != '' else 0
                resolution = factor_f
                if option == "Min":
                    le.setText(str(minv_f))
                elif option == "Max":
                    le.setText(str(maxv_f))
                elif option == "Mid":
                    le.setText(str((minv_f + maxv_f) / 2))
                elif option == "Min - Res":
                    le.setText(str(minv_f - resolution))
                elif option == "Min + Res":
                    le.setText(str(minv_f + resolution))
                elif option == "Max - Res":
                    le.setText(str(maxv_f - resolution))
                elif option == "Max + Res":
                    le.setText(str(maxv_f + resolution))
                elif option == "Custom":
                    # Không thay đổi, giữ nguyên giá trị hiện tại
                    pass
            except Exception:
                le.setText("0")

    def generate_payload(self):
        sigs = []
        for i, row in self.signals.iterrows():
            val = self.table.cellWidget(i, 1).text()
            factor = row['dbc_Factor']
            offset = row['dbc_Offset']
            minv = row['dbc_Minimum']
            maxv = row['dbc_Maximum']
            raw = calc_signal_raw(val, factor, offset, minv, maxv)
            sig = row.to_dict()
            sig['raw_value'] = raw
            sigs.append(sig)
            # Hiển thị raw value ở cột "Actual Simualte Value"
            self.table.setItem(i, 9, QTableWidgetItem(str(raw)))
        payload = build_payload(sigs, self.total_len)
        # Không cần setText cho self.payload_edit nữa
        return payload

    def filter_messages(self, text):
        self.msg_combo.blockSignals(True)
        self.msg_combo.clear()
        filtered = [m for m in self.all_messages if text.lower() in m.lower()]
        self.msg_combo.addItems(filtered)
        self.msg_combo.blockSignals(False)
        if filtered:
            self.load_signals(filtered[0])

    def create_eth_packet_auto(self):
        # Nếu chưa chọn source, hỏi chọn folder source
        if not self.source_selector.source_folder:
            try:
                variants = self.source_selector.select_source_folder(self)
                variant = self.source_selector.choose_variant(self)
                self.autosar_root = os.path.join(self.source_selector.source_folder, "Autosar")
                self.variant = variant
                parent = self.source_selector.source_folder
                base_candidates = [d for d in os.listdir(parent) if d.startswith("BaseSystemCore") and os.path.isdir(os.path.join(parent, d))]
                if not base_candidates:
                    raise Exception("Không tìm thấy thư mục BaseSystemCore* ở cùng cấp với Autosar.")
                self.base_system = base_candidates[0]
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", str(e))
                return

        # Lấy payload hiện tại
        payload_hex = self.generate_payload()
        payload_bytes = bytes.fromhex(payload_hex)
        message_name = self.msg_combo.currentText()
        try:
            src_mac, dst_mac, src_ip, dst_ip, message_id = get_eth_info(
                self.source_selector.source_folder, self.base_system, self.variant, message_name
            )
            if not src_mac or not dst_mac:
                raise ValueError("Không lấy được địa chỉ MAC từ file variant.")
            src_port = 42557
            dst_port = 42557
            builder = EthernetPacketBuilder(
                src_mac=src_mac,
                dst_mac=dst_mac,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                message_id=message_id,
                raw_payload=payload_bytes
            )
            eth_packet = builder.build()
            # Hiển thị chi tiết packet bằng widget mới
            self.show_packet_detail(eth_packet, src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port, message_id, payload_bytes)
            QMessageBox.information(self, "Ethernet Packet", "Đã tạo Ethernet Packet thành công!")
            self.last_eth_packet = eth_packet
            self.last_dst_ip = dst_ip
            self.last_dst_port = dst_port
            self.last_payload = payload_bytes
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lỗi tạo ETH Packet: {e}")
            print(e)

    def show_packet_detail(self, eth_packet, src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port, message_id, payload_bytes):
        # Phân tích eth_packet thành các trường để truyền vào PacketDetailWidget
        # Ethernet header: 14 bytes, IPv4: 20 bytes, UDP: 8 bytes, Autosar PDU: còn lại
        eth_hdr = eth_packet[:14]
        ip_hdr = eth_packet[14:34]
        udp_hdr = eth_packet[34:42]
        pdu_payload = eth_packet[42:]

        # Ethernet
        ethernet = {
            "destination": ':'.join(f"{b:02X}" for b in eth_hdr[:6]),
            "source": ':'.join(f"{b:02X}" for b in eth_hdr[6:12]),
            "eth_type": f"0x{eth_hdr[12:14].hex().upper()}"
        }

        # IPv4
        version_ihl = ip_hdr[0]
        version = version_ihl >> 4
        ihl = version_ihl & 0x0F
        total_length = int.from_bytes(ip_hdr[2:4], 'big')
        identification = int.from_bytes(ip_hdr[4:6], 'big')
        flags_fragment = int.from_bytes(ip_hdr[6:8], 'big')
        flags = {
            "reserved": bool(flags_fragment & 0x8000),
            "dont_fragment": bool(flags_fragment & 0x4000),
            "more_fragments": bool(flags_fragment & 0x2000)
        }
        fragment_offset = flags_fragment & 0x1FFF
        ttl = ip_hdr[8]
        protocol = ip_hdr[9]
        checksum = f"0x{int.from_bytes(ip_hdr[10:12], 'big'):04X}"
        source_ip = '.'.join(str(b) for b in ip_hdr[12:16])
        destination_ip = '.'.join(str(b) for b in ip_hdr[16:20])
        ipv4 = {
            "version": version,
            "header_length": ihl,
            "total_length": total_length,
            "identification": identification,
            "flags": flags,
            "fragment_offset": fragment_offset,
            "ttl": ttl,
            "protocol": protocol,
            "checksum": checksum,
            "source_ip": source_ip,
            "destination_ip": destination_ip
        }

        # UDP
        udp = {
            "source_port": int.from_bytes(udp_hdr[0:2], 'big'),
            "destination_port": int.from_bytes(udp_hdr[2:4], 'big'),
            "length": int.from_bytes(udp_hdr[4:6], 'big'),
            "checksum": f"0x{int.from_bytes(udp_hdr[6:8], 'big'):04X}"
        }

        # Payload là Autosar PDU (bỏ qua 8 bytes đầu là message_id + length)
        payload = pdu_payload[8:]
        raw = eth_packet

        self.packet_detail_widget.set_packet_data(
            ethernet=ethernet,
            ipv4=ipv4,
            udp=udp,
            payload=payload,
            raw=raw
        )

    def send_eth_packet(self):
        try:
            eth_payload = getattr(self, 'last_payload', None)
            if not eth_payload:
                QMessageBox.warning(self, "Lỗi", "Bạn cần tạo ETH Packet trước!")
                return
            # Lấy thông tin IP/port từ lần build gần nhất (hoặc lưu lại khi build)
            dst_ip = self.last_dst_ip if hasattr(self, 'last_dst_ip') else "192.168.0.2"
            dst_port = self.last_dst_port if hasattr(self, 'last_dst_port') else 42557
            print(dst_ip)
            print(dst_port)
            print(eth_payload)
            # Gửi payload qua UDP
            send_udp_packet(dst_ip, dst_port, eth_payload)
            QMessageBox.information(self, "Gửi thành công", "Đã gửi ETH Packet ra test bench (UDP)!")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Gửi thất bại: {e}")

    def create_capl_node_action(self):
        # Kiểm tra xem đã có payload chưa (tức là đã nhấn "Tạo ETH Packet" trước đó)
        payload_hex = getattr(self, 'last_payload', None)
        if payload_hex is None:
            QMessageBox.warning(self, "Lỗi", "Bạn cần tạo Packet trước khi tạo CAPL node! Hãy nhấn 'Tạo ETH Packet' trước.")
            return
        message_name = self.msg_combo.currentText()
        signals, total_len = get_signals(self.df, message_name)
        payload_bytes = self.last_payload
        # Lấy lại các trường Ethernet/IP cần thiết
        try:
            src_mac, dst_mac, src_ip, dst_ip, message_id = get_eth_info(
                self.source_selector.source_folder, self.base_system, self.variant, message_name
            )
            eth_type = 0x0800
            builder = EthernetPacketBuilder(
                src_mac=src_mac,
                dst_mac=dst_mac,
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=42557,
                dst_port=42557,
                message_id=message_id,
                raw_payload=payload_bytes
            )
            eth_packet = builder.build()
            ipv4_payload_bytes = eth_packet[14:]  # Bỏ 14 bytes Ethernet header

            # Hỏi người dùng chọn nơi lưu file output
            from PyQt5.QtWidgets import QFileDialog
            suggested_name = f"ETH_Node_{message_name}.capl"
            output_path, _ = QFileDialog.getSaveFileName(
                self, "Chọn nơi lưu file CAPL node", suggested_name, "CAPL Files (*.can);;All Files (*)"
            )
            if not output_path:
                return

            template_path = os.path.join(os.path.dirname(__file__), "template", "ETH_Packet_builder.can")
            create_capl_node(
                template_path=template_path,
                output_path=output_path,
                dbc_message=message_name,
                total_length=len(ipv4_payload_bytes),
                src_mac=src_mac,
                dst_mac=dst_mac,
                eth_type=eth_type,
                ipv4_payload_bytes=ipv4_payload_bytes
            )
            QMessageBox.information(self, "Tạo CAPL Node", f"Đã tạo file CAPL node:\n{output_path}")
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Lỗi tạo CAPL node: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())

