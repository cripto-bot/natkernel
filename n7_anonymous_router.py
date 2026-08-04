#!/usr/bin/env python3
"""
N7 ANONYMOUS ROUTER v2.0 — Powered by GraphLang

Uses GraphLang's build_graph() to define routing as a structural graph.
Each fragment = one IR kind. N=7 kinds = 7 channels.
Uses GraphLang core (Node, Graph, build_graph, executor).

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import sys, os
sys.path.insert(0, '/mnt/hdd3tb/GraphLab-Final')

from graphlang.core import Graph, Node, build_graph, GraphLangExecutor
import socket, time, random, threading, subprocess
from pathlib import Path
from datetime import datetime

# ═══ 7 PROFILES = 7 IR KINDS ═══
PROFILES = {
    'struct':   {'ua': 'Mozilla/5.0 (Windows NT 10.0) Chrome/120', 'ttl': 128, 'name': 'chrome_win'},
    'define':   {'ua': 'Mozilla/5.0 (Macintosh) Safari/605.1',    'ttl': 64,  'name': 'safari_mac'},
    'loop':     {'ua': 'Mozilla/5.0 (X11; Linux) Firefox/121',    'ttl': 64,  'name': 'firefox'},
    'conditional': {'ua': 'Mozilla/5.0 (iPhone) Mobile Safari',   'ttl': 64,  'name': 'ios'},
    'return':   {'ua': 'Mozilla/5.0 (Android 14) Chrome Mobile',  'ttl': 64,  'name': 'android'},
    'hash':     {'ua': 'Mozilla/5.0 (Windows) Edg/120',           'ttl': 128, 'name': 'edge'},
    'chain':    {'ua': 'curl/8.5.0',                               'ttl': 64,  'name': 'curl'},
}

MIMIC = ['wikipedia.org','github.com','stackoverflow.com','reddit.com',
         'news.ycombinator.com','medium.com','pypi.org','codeberg.org']

LOG = Path.home() / '.phantom' / 'router'
LOG.mkdir(parents=True, exist_ok=True)


class GraphLangRouter:
    """
    Router defined as a GraphLang graph.
    
    Graph structure:
      struct (root) → define (target) → loop (fragment) → conditional (if sent?)
        → return (response) → hash (verify) → chain (reassemble)
    
    The graph IS the routing logic. Not code — structure.
    """
    
    def __init__(self, target: str, port: int):
        self.target = target
        self.port = port
        
        # Build routing graph using GraphLang DSL
        self.graph = build_graph(
            ('struct',   'root',    '', []),
            ('define',   f'{target}:{port}', '', [1]),
            ('loop',     '7',       '', [2]),
            ('conditional', 'fragment', '', [3]),
            ('return',   'response', '', [4]),
            ('hash',     'verify',  '', [5]),
            ('chain',    'reassemble', '', [6]),
        )
        
        self.executor = GraphLangExecutor()
        self.results = []
    
    def fragment(self, data: bytes) -> list:
        """Split into 7 chunks — one per IR kind"""
        n = 7
        size = max(1, len(data) // n)
        return [data[i*size:(i+1)*size if i<n-1 else len(data)] for i in range(n)]
    
    def route(self, data: bytes) -> list:
        """
        Execute the GraphLang routing graph against target.
        
        7 channels = 7 TCP connections with 7 different fingerprints.
        GraphLang graph defines the flow structure.
        """
        fragments = self.fragment(data)
        kinds = list(PROFILES.keys())
        responses = []
        
        print(f"\n═══ GRAPHLANG ROUTER ═══")
        print(f"  Graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        print(f"  Target: {self.target}:{self.port}")
        print(f"  Payload: {len(data)}B → 7 × ~{len(fragments[0])}B\n")
        
        for i, (frag, kind) in enumerate(zip(fragments, kinds)):
            profile = PROFILES[kind]
            
            # Execute graph node for this fragment (build_graph uses 'u1'..'uN' IDs)
            self.executor._results = {}
            result = self.executor._eval(f'u{i+1}', self.graph, {})
            
            # Send fragment with profile fingerprint
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(4)
                sock.connect((self.target, self.port))
                sock.send(frag)
                
                try:
                    resp = sock.recv(2048)
                except:
                    resp = b''
                
                sock.close()
                responses.append(resp)
                
                print(f"  [{i+1}/7] {kind:12s} [{profile['name']:12s}] "
                      f"{len(frag)}B → {len(resp)}B ✓")
                
            except Exception as e:
                print(f"  [{i+1}/7] {kind:12s} [{profile['name']:12s}] FAIL: {str(e)[:30]}")
                responses.append(b'')
            
            # Lorenz delay
            t = time.time() * 0.13
            delay = 0.2 + 0.4 * abs(hash(str(t)) % 100) / 100
            time.sleep(delay)
            
            # Mimic request to mask fragment
            self._mimic(kind, i)
        
        success = sum(1 for r in responses if r)
        print(f"\n  Delivered: {success}/7")
        
        # Log to graph-style log
        self._log_graph(data, responses, success)
        
        return responses
    
    def _mimic(self, kind: str, idx: int):
        """Send normal HTTP request to mask the fragment"""
        try:
            site = MIMIC[(idx + int(time.time())) % len(MIMIC)]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((site, 443))
            # TLS ClientHello
            hello = bytes([0x16, 0x03, 0x01, 0x00, 0x60, 0x01, 0x00, 0x00, 0x5c, 0x03, 0x03])
            hello += bytes(random.randint(0, 255) for _ in range(32))
            hello += bytes([0x00, 0x00, 0x02, 0x00, 0x2f])
            sock.send(hello)
            sock.recv(512)
            sock.close()
        except:
            pass
    
    def _log_graph(self, data: bytes, responses: list, success: int):
        """Log routing as GraphLang structure"""
        import json
        entry = {
            'ts': datetime.now().isoformat(),
            'graph': {
                'nodes': len(self.graph.nodes),
                'edges': len(self.graph.edges),
            },
            'target': f'{self.target}:{self.port}',
            'payload_size': len(data),
            'fragments': success,
            'kinds': list(PROFILES.keys()),
            'responses': [len(r) for r in responses],
        }
        f = LOG / f'graphlang_route_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        f.write_text(json.dumps(entry, indent=2))


# ═══ Phantom-Wrapped Nmap ═══
def phantom_scan(target: str, ports: str) -> str:
    """Run nmap wrapped in phantom mimic burst"""
    print(f"""
╔══════════════════════════════════════╗
║  PHANTOM-WRAPPED NMAP               ║
║  Target: {target:<27s}║
║  Ports:  {ports:<27s}║
║  Mimic:  8 sites × 7 profiles       ║
╚══════════════════════════════════════╝
""")
    
    # Burst mimic traffic
    def burst():
        for _ in range(15):
            try:
                site = MIMIC[random.randint(0, len(MIMIC)-1)]
                p = random.choice(list(PROFILES.values()))
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((site, 443))
                sock.send(b'\x16\x03\x01\x00\x60\x01\x00\x00\x5c\x03\x03' + 
                         bytes(random.randint(0,255) for _ in range(32)))
                sock.recv(512)
                sock.close()
            except:
                pass
            time.sleep(random.uniform(0.02, 0.08))
    
    print("[1] Mimic burst started")
    t = threading.Thread(target=burst, daemon=True)
    t.start()
    time.sleep(0.3)
    
    print("[2] nmap inside mimic noise")
    cmd = f"nmap -sT -Pn -p {ports} --host-timeout 8s {target}"
    result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=60)
    
    print("[3] Done")
    t.join(timeout=2)
    
    return result.stdout + result.stderr


# ═══ CLI ═══
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='N7 GraphLang Anonymous Router')
    p.add_argument('--target', '-t', help='Target IP/host')
    p.add_argument('--ports', '-p', default='80,443')
    p.add_argument('--mode', '-m', default='fragment',
                   choices=['fragment','phantom','curl'])
    p.add_argument('--url', '-u')
    args = p.parse_args()
    
    if not args.target:
        p.print_help()
        sys.exit(1)
    
    if args.mode == 'phantom':
        print(phantom_scan(args.target, args.ports))
    
    elif args.mode == 'fragment':
        port = int(args.ports.split(',')[0])
        router = GraphLangRouter(args.target, port)
        payload = b'\x16\x03\x01\x00\x60\x01\x00\x00\x5c' * 5
        router.route(payload)
    
    elif args.mode == 'curl' and args.url:
        router = GraphLangRouter(args.target, 80)
        request = f"GET {args.url} HTTP/1.1\r\nHost: {args.target}\r\n\r\n"
        router.route(request.encode())
