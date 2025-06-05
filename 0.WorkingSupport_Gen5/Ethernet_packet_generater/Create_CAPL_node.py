import os

def create_capl_node(
    template_path,
    output_path,
    dbc_message,
    total_length,
    src_mac,
    dst_mac,
    eth_type,
    ipv4_payload_bytes
):
    # Đọc template
    with open(template_path, encoding="utf-8") as f:
        template = f.read()

    # Chuyển src_mac, dst_mac thành dạng 02:7D:FA:00:BD:00
    src_mac_str = src_mac.upper()
    dst_mac_str = dst_mac.upper()
    eth_type_hex = f"0x{eth_type:04X}"

    # IPv4_Payload: từ header IPv4 đến hết, mỗi byte 0xHH, cách nhau bởi dấu phẩy, đặt trong dấu ""
    ipv4_payload_str = ",".join(f"0x{b:02X}" for b in ipv4_payload_bytes)

    # Thay thế các trường trong template (dùng dấu <...> đúng với template)
    content = template
    content = content.replace("<dbc_message>", dbc_message)
    content = content.replace("<total_length>", str(total_length))
    content = content.replace("<src_mac>", src_mac_str)
    content = content.replace("<dst_mac>", dst_mac_str)
    content = content.replace("<eth_type>", eth_type_hex)
    content = content.replace("<IPv4_Payload>", ipv4_payload_str)

    # Ghi ra file output
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)


