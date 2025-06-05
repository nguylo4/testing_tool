import os
import re

def get_sensor_ids_from_message(message_name):
    # NR_RL: ECU0 -> ECU1, NR_RR: ECU1 -> ECU0
    if "NR_RL" in message_name:
        return "ECU0", "ECU1"
    elif "NR_RR" in message_name:
        return "ECU1", "ECU0"
    else:
        # default
        return "ECU0", "ECU1"

def parse_mac_from_variant_c(variant_c_path, ecu):
    if not os.path.isfile(variant_c_path):
        raise FileNotFoundError(f"Không tìm thấy file: {variant_c_path}")
    with open(variant_c_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # Tìm đúng function body
    m = re.search(r'void\s+Bsc0_VariantQm_AssignMACAddress\s*\([^)]*\)\s*\{(.+?)\n\}', content, re.DOTALL)
    if not m:
        raise ValueError(f"Không tìm thấy hàm Bsc0_VariantQm_AssignMACAddress trong {variant_c_path}")
    body = m.group(1)
    # Tìm khởi tạo macAddr
    mac_init = re.search(r'macAddr\s*\[\s*\d+\s*\]\s*=\s*\{\s*([^\}]+)\}', body)
    if not mac_init:
        raise ValueError(f"Không tìm thấy khởi tạo macAddr trong {variant_c_path}")
    mac_bytes = [int(x.strip().replace('u','').replace('0x',''),16) for x in mac_init.group(1).split(',')]
    # Tìm switch-case trong function
    cases = dict(re.findall(r'case\s+SENSORID_(ECU\d+):\s*macAddr\[4\]\s*=\s*0x([0-9A-Fa-f]+)u;', body))
    mac4 = int(cases.get(ecu, 'BD'), 16)
    mac_bytes[4] = mac4
    return ':'.join(f"{b:02X}" for b in mac_bytes)

def parse_ip_from_bswm(bswm_path, ecu):
    if not os.path.isfile(bswm_path):
        raise FileNotFoundError(f"Không tìm thấy file: {bswm_path}")
    with open(bswm_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # Tìm đúng function BswM_AssignIpAddress với mọi kiểu khai báo
    m = re.search(
        r'(?:void|FUNC\s*\(\s*void\s*,\s*\w+\s*\))\s+BswM_AssignIpAddress\s*\([^)]*\)\s*\{([\s\S]+?)\n\}',
        content
    )
    if not m:
        funcs = re.findall(r'(?:void|FUNC\s*\(\s*void\s*,\s*\w+\s*\))\s+\w+\s*\([^)]*\)\s*\{', content)
        raise ValueError(f"Không tìm thấy hàm BswM_AssignIpAddress trong {bswm_path}. Các hàm có trong file: {funcs}")
    body = m.group(1)
    cases = dict(re.findall(r'case\s+SENSORID_(ECU\d+):\s*localAddr\.addr\[0\]\s*=\s*0x([0-9A-Fa-f]+)UL;', body))
    ip_hex = cases.get(ecu)
    if not ip_hex:
        default = re.search(r'default:[^;]*localAddr\.addr\[0\]\s*=\s*0x([0-9A-Fa-f]+)UL;', body)
        ip_hex = default.group(1) if default else '0100A8C0'
    ip_bytes = bytes.fromhex(ip_hex)
    ip_str = '.'.join(str(b) for b in ip_bytes[::-1])
    return ip_str

def parse_message_id_from_soad(soad_path, message_name):
    with open(soad_path, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    # Tìm struct SoAd_PduRouteDest
    # Tìm dòng chứa message_name
    m = re.search(r'\{\s*/\*\s*\d+\s*\*/\s*0x([0-9A-Fa-f]+)u,.*\}\s*,\s*/\*\s*\[.*' + re.escape(message_name) + r'[^*]*\*/', content)
    if not m:
        return None
    return int(m.group(1), 16)

# Ví dụ sử dụng:
def get_eth_info(source_root, base, variant, message_name):
    ecu_src, ecu_dst = get_sensor_ids_from_message(message_name)
    # Đường dẫn file MAC
    variant_c = os.path.join(source_root, base, variant, "Bsc0_Qm", "Bsc0_VariantQm.c")
    # Đường dẫn file IP và message_id
    autosar_root = os.path.join(source_root, "Autosar")
    bswm_c = os.path.join(autosar_root, variant, "Integration", "BswM", "BswM_Callout_Stubs.c")
    soad_c = os.path.join(autosar_root, variant, "Config", "SoAd", "SoAd_Lcfg.c")
    src_mac = parse_mac_from_variant_c(variant_c, ecu_src)
    dst_mac = parse_mac_from_variant_c(variant_c, ecu_dst)
    src_ip = parse_ip_from_bswm(bswm_c, ecu_src)
    dst_ip = parse_ip_from_bswm(bswm_c, ecu_dst)
    message_id = parse_message_id_from_soad(soad_c, message_name)
    return src_mac, dst_mac, src_ip, dst_ip, message_id
    