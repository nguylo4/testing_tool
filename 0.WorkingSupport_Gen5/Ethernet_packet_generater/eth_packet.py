import struct
import socket

class EthernetPacketBuilder:
    def __init__(self, src_mac, dst_mac, src_ip, dst_ip, src_port, dst_port, message_id, raw_payload):
        self.src_mac = self.mac_to_bytes(src_mac)
        self.dst_mac = self.mac_to_bytes(dst_mac)
        self.src_ip = socket.inet_aton(src_ip)
        self.dst_ip = socket.inet_aton(dst_ip)
        self.src_port = src_port
        self.dst_port = dst_port
        self.message_id = message_id
        self.raw_payload = raw_payload

    def mac_to_bytes(self, mac_str):
        return bytes.fromhex(mac_str.replace(":", ""))

    def checksum(self, data):
        if len(data) % 2:
            data += b'\x00'
        res = sum(struct.unpack("!%dH" % (len(data) // 2), data))
        while res > 0xffff:
            res = (res & 0xffff) + (res >> 16)
        return ~res & 0xffff

    def build_ethernet_header(self):
        eth_type = b'\x08\x00'  # IPv4
        return self.dst_mac + self.src_mac + eth_type

    def build_ipv4_header(self, total_length):
        version_ihl = (4 << 4) + 5
        dscp_ecn = 0
        identification = 54321
        flags_fragment_offset = 0b010 << 13  # Don't Fragment
        ttl = 64
        protocol = 17  # UDP
        header_checksum = 0  # to be calculated later

        ip_header = struct.pack('!BBHHHBBH4s4s',
                                version_ihl,
                                dscp_ecn,
                                total_length,
                                identification,
                                flags_fragment_offset,
                                ttl,
                                protocol,
                                header_checksum,
                                self.src_ip,
                                self.dst_ip)

        checksum_value = self.checksum(ip_header)
        ip_header = struct.pack('!BBHHHBBH4s4s',
                                version_ihl,
                                dscp_ecn,
                                total_length,
                                identification,
                                flags_fragment_offset,
                                ttl,
                                protocol,
                                checksum_value,
                                self.src_ip,
                                self.dst_ip)
        return ip_header

    def build_udp_header(self, length, pseudo_header):
        checksum = 0
        udp_header = struct.pack('!HHHH', self.src_port, self.dst_port, length, checksum)
        pseudo_packet = pseudo_header + udp_header + self.build_autosar_pdu()
        udp_checksum = self.checksum(pseudo_packet)
        udp_header = struct.pack('!HHHH', self.src_port, self.dst_port, length, udp_checksum)
        return udp_header

    def build_autosar_pdu(self):
        id_bytes = struct.pack('!I', self.message_id)
        length_bytes = struct.pack('!I', len(self.raw_payload))
        return id_bytes + length_bytes + self.raw_payload

    def build(self):
        pdu_payload = self.build_autosar_pdu()
        udp_len = 8 + len(pdu_payload)
        ip_len = 20 + udp_len

        ip_header = self.build_ipv4_header(ip_len)

        pseudo_header = self.src_ip + self.dst_ip + struct.pack('!BBH', 0, 17, udp_len)
        udp_header = self.build_udp_header(udp_len, pseudo_header)

        ethernet_header = self.build_ethernet_header()

        return ethernet_header + ip_header + udp_header + pdu_payload

def send_udp_packet(ip, port, data):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.sendto(data, (ip, port))
    s.close()