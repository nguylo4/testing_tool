from PyQt5.QtWidgets import (QWidget, QLabel, QVBoxLayout, QFormLayout, QTextEdit, QGroupBox, QApplication, QHBoxLayout)
from PyQt5.QtGui import QFont
import sys

class EthernetHeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.destination_label = QLabel()
        self.source_label = QLabel()
        self.type_label = QLabel()

        layout.addRow("Destination:", self.destination_label)
        layout.addRow("Source:", self.source_label)
        layout.addRow("Type:", self.type_label)
        self.setLayout(layout)

    def set_data(self, destination, source, eth_type):
        self.destination_label.setText(destination)
        self.source_label.setText(source)
        self.type_label.setText(eth_type)

class IPv4HeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.labels = {}
        fields = ["version", "header_length", "total_length", "identification",
                  "flags", "fragment_offset", "ttl", "protocol",
                  "checksum", "source_ip", "destination_ip"]

        for field in fields:
            self.labels[field] = QLabel()
            layout.addRow(field.replace("_", " ").title() + ":", self.labels[field])

        self.setLayout(layout)

    def set_data(self, data: dict):
        for key, label in self.labels.items():
            if key == "flags":
                flags = data.get("flags", {})
                text = ", ".join([k for k, v in flags.items() if v])
                label.setText(text)
            else:
                label.setText(str(data.get(key, "")))

class UDPHeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QFormLayout()
        self.source_port_label = QLabel()
        self.destination_port_label = QLabel()
        self.length_label = QLabel()
        self.checksum_label = QLabel()

        layout.addRow("Source Port:", self.source_port_label)
        layout.addRow("Destination Port:", self.destination_port_label)
        layout.addRow("Length:", self.length_label)
        layout.addRow("Checksum:", self.checksum_label)
        self.setLayout(layout)

    def set_data(self, source_port, destination_port, length, checksum):
        self.source_port_label.setText(str(source_port))
        self.destination_port_label.setText(str(destination_port))
        self.length_label.setText(str(length))
        self.checksum_label.setText(checksum)

class PayloadWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.text_edit = QTextEdit()
        self.text_edit.setFont(QFont("Courier"))
        self.text_edit.setReadOnly(True)
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

    def set_data(self, payload_bytes: bytes):
        lines = []
        for i in range(0, len(payload_bytes), 16):
            chunk = payload_bytes[i:i+16]
            hex_part = ' '.join(f"{b:02X}" for b in chunk)
            # ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            # lines.append(f"{i:08X}  {hex_part:<48}  {ascii_part}")
            lines.append(hex_part)
        self.text_edit.setPlainText('\n'.join(lines))

class PacketDetailWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.ethernet_widget = EthernetHeaderWidget()
        self.ipv4_widget = IPv4HeaderWidget()
        self.udp_widget = UDPHeaderWidget()
        self.payload_widget = PayloadWidget()
        self.raw_widget = PayloadWidget()

        layout.addWidget(self._wrap_group("Ethernet", self.ethernet_widget))
        layout.addWidget(self._wrap_group("IPv4", self.ipv4_widget))
        layout.addWidget(self._wrap_group("UDP", self.udp_widget))
        layout.addWidget(self._wrap_group("Payload", self.payload_widget))
        layout.addWidget(self._wrap_group("Raw Frame", self.raw_widget))

        self.setLayout(layout)

    def _wrap_group(self, title, widget):
        group = QGroupBox(title)
        vbox = QVBoxLayout()
        vbox.addWidget(widget)
        group.setLayout(vbox)
        return group

    def set_packet_data(self, ethernet, ipv4, udp, payload, raw):
        self.ethernet_widget.set_data(**ethernet)
        self.ipv4_widget.set_data(ipv4)
        self.udp_widget.set_data(**udp)
        self.payload_widget.set_data(payload)
        self.raw_widget.set_data(raw)

# Sample test
# if __name__ == "__main__":
#     app = QApplication(sys.argv)

#     window = PacketDetailWidget()
#     window.set_packet_data(
#         ethernet={"destination": "02:7D:FA:00:BE:00", "source": "02:7D:FA:00:BD:00", "eth_type": "0x0800"},
#         ipv4={
#             "version": 4,
#             "header_length": 5,
#             "total_length": 100,
#             "identification": 54321,
#             "flags": {"reserved": False, "dont_fragment": True, "more_fragments": False},
#             "fragment_offset": 0,
#             "ttl": 64,
#             "protocol": 17,
#             "checksum": "0xE503",
#             "source_ip": "192.168.0.1",
#             "destination_ip": "192.168.0.2"
#         },
#         udp={"source_port": 42557, "destination_port": 42557, "length": 80, "checksum": "0x861A"},
#         payload=bytes.fromhex("000000039FF90000...".replace("...", "D4C7CBE3E4")),
#         raw=bytes.fromhex("027DFA00BE00...".replace("...", "46FC3F05E9"))
#     )

#     window.resize(800, 800)
#     window.show()
#     sys.exit(app.exec_())
