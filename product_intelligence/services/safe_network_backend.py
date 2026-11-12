import ipaddress
import socket

import httpcore


class SafeNetworkBackend(httpcore.SyncBackend):
    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None):
        addresses = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        public_addresses = []
        for family, kind, proto, canonname, sockaddr in addresses:
            address = ipaddress.ip_address(sockaddr[0])
            if not address.is_global:
                raise httpcore.ConnectError("Adresse reseau non publique interdite")
            public_addresses.append(address.compressed)
        if not public_addresses:
            raise httpcore.ConnectError("Aucune adresse publique disponible")
        return super().connect_tcp(public_addresses[0], port, timeout=timeout, local_address=local_address, socket_options=socket_options)
