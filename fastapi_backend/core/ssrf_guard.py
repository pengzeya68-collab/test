import ipaddress
import socket
from urllib.parse import urlparse


def _is_ssrf_guard_disabled() -> bool:
    """检查是否临时禁用了 SSRF 防护"""
    try:
        from fastapi_backend.core.config import settings
        return settings.DISABLE_SSRF_GUARD
    except Exception:
        return False


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
    # 临时禁用 SSRF 防护时直接放行
    if _is_ssrf_guard_disabled():
        return True, ""
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
                ip_obj = ipaddress.ip_address(sockaddr[0])
                # 处理 IPv4-mapped IPv6 地址（如 ::ffff:127.0.0.1）
                if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
                    ip_obj = ip_obj.ipv4_mapped
                for network in BLOCKED_NETWORKS:
                    if ip_obj in network:
                        return False, f"不允许访问内网地址 {ip_obj}"
        except socket.gaierror:
            return False, f"无法解析主机名: {hostname}"
        return True, ""
    except Exception as e:
        return False, f"URL 解析失败: {e}"
