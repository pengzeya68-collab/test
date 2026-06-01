import ipaddress
import socket
from urllib.parse import urlparse

BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]

BLOCKED_HOSTS = {"localhost", "host.docker.internal"}


def validate_url_safety(url: str) -> tuple[bool, str]:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            return False, "URL 缺少主机名"
        if hostname.lower() in BLOCKED_HOSTS:
            return False, f"不允许访问 {hostname}"
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in resolved:
                ip = ipaddress.ip_address(sockaddr[0])
                for network in BLOCKED_NETWORKS:
                    if ip in network:
                        return False, f"不允许访问内网地址 {ip}"
        except socket.gaierror:
            return False, f"无法解析主机名: {hostname}"
        return True, ""
    except Exception as e:
        return False, f"URL 解析失败: {e}"
