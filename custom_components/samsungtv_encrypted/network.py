"""Small network helpers for SamsungTV Encrypted."""
import socket

ARP_PATH = "/proc/net/arp"


def _parse_proc_net_arp(text, host):
    rows = [line.split() for line in text.splitlines()[1:]]
    for row in rows:
        if len(row) >= 4 and row[0] == host and row[3] != "00:00:00:00:00:00":
            return row[3].lower()
    return None


def get_arp_mac(host, arp_path=ARP_PATH):
    """Return a cached IPv4 ARP MAC address for host, if available."""
    try:
        ip_address = socket.gethostbyname(host)
    except OSError:
        return None

    # ponytail: /proc/net/arp is Linux/IPv4/cache-only; use HA network APIs or
    # active neighbor discovery if we ever need cross-platform certainty.
    try:
        with open(arp_path, encoding="utf-8") as arp_file:
            return _parse_proc_net_arp(arp_file.read(), ip_address)
    except OSError:
        return None


if __name__ == "__main__":
    sample = (
        "IP address       HW type     Flags       HW address            Mask     Device\n"
        "192.0.2.10       0x1         0x2         AA:BB:CC:DD:EE:FF     *        eth0\n"
    )
    assert _parse_proc_net_arp(sample, "192.0.2.10") == "aa:bb:cc:dd:ee:ff"
    assert _parse_proc_net_arp(sample, "192.0.2.11") is None
