#!/usr/bin/env python3
"""
N7 HONEYPOT RPC v1.0 — Ethereum/Solana Node Emulator
Wallets come to us. We analyze their structure. They never know.

Listens on port 8545 (ETH) + 8899 (SOL).
Responds like a real node. Logs everything.
N=7 stealth. Zero detection.

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""
import json, socket, threading, time, hashlib, secrets
from pathlib import Path
from datetime import datetime

LOG_DIR = Path.home() / '.phantom' / 'honeypot'
LOG_DIR.mkdir(parents=True, exist_ok=True)

class N7Honeypot:
    def __init__(self, port: int = 8545, chain: str = "ethereum"):
        self.port = port
        self.chain = chain
        self.interactions = []
        self.wallets_seen = set()
        
    def _fake_block_number(self) -> str:
        return hex(20000000 + int(time.time() % 10000))
    
    def _fake_balance(self) -> str:
        return hex(10**18 + secrets.randbits(64))  # ~1 ETH + random
    
    def _fake_gas_price(self) -> str:
        return hex(20 * 10**9)  # 20 gwei
    
    def _handle_request(self, data: bytes, addr: tuple) -> bytes:
        """Process JSON-RPC request and respond like a real node."""
        try:
            request = json.loads(data)
            method = request.get('method', '')
            req_id = request.get('id', 0)
            params = request.get('params', [])
            
            # Log the interaction
            entry = {
                'ts': datetime.now().isoformat(),
                'ip': addr[0],
                'port': addr[1],
                'method': method,
                'params': str(params)[:200],
                'chain': self.chain,
            }
            self.interactions.append(entry)
            
            # Extract wallet addresses
            for p in params:
                if isinstance(p, str) and p.startswith('0x') and len(p) == 42:
                    self.wallets_seen.add(p)
                    entry['wallet'] = p
            
            # Build response based on method
            result = None
            if method == 'eth_blockNumber':
                result = self._fake_block_number()
            elif method == 'eth_getBalance':
                result = self._fake_balance()
            elif method == 'eth_gasPrice':
                result = self._fake_gas_price()
            elif method == 'eth_chainId':
                result = '0x1'
            elif method == 'net_version':
                result = '1'
            elif method == 'eth_sendRawTransaction':
                result = '0x' + secrets.token_hex(32)
                entry['tx_sent'] = True
            elif method == 'eth_call':
                result = '0x' + secrets.token_hex(32)
            else:
                result = '0x' + secrets.token_hex(32)
            
            response = {
                'jsonrpc': '2.0',
                'id': req_id,
                'result': result,
            }
            
            # Save every 10 interactions
            if len(self.interactions) % 10 == 0:
                self._save()
            
            wallet_tag = f" [wallet: {entry.get('wallet','?')[:10]}]" if 'wallet' in entry else ""
            print(f"  [{addr[0]}:{addr[1]}] {method}{wallet_tag}")
            
            return json.dumps(response).encode()
            
        except Exception as e:
            return json.dumps({'jsonrpc':'2.0','id':0,'error':str(e)}).encode()
    
    def _save(self):
        """Save interactions to disk."""
        report = {
            'chain': self.chain,
            'port': self.port,
            'interactions': len(self.interactions),
            'wallets_seen': list(self.wallets_seen),
            'last': self.interactions[-10:] if self.interactions else [],
        }
        f = LOG_DIR / f'honeypot_{self.chain}_{self.port}.json'
        f.write_text(json.dumps(report, indent=2))
        f.chmod(0o600)
    
    def start(self):
        """Start honeypot server."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('0.0.0.0', self.port))
        sock.listen(5)
        sock.settimeout(1)
        
        print(f"[HONEYPOT] {self.chain} RPC on port {self.port}")
        self.running = True
        
        while self.running:
            try:
                conn, addr = sock.accept()
                data = conn.recv(4096)
                if data:
                    response = self._handle_request(data, addr)
                    conn.send(response)
                conn.close()
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    print(f"  [!] {e}")
        
        sock.close()
    
    def stop(self):
        self.running = False
        self._save()
        print(f"\n═══ HONEYPOT STOPPED ═══")
        print(f"  Chain: {self.chain}")
        print(f"  Interactions: {len(self.interactions)}")
        print(f"  Wallets: {len(self.wallets_seen)}")

# ═══ MAIN ═══
if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════╗
║   N7 HONEYPOT RPC v1.0                   ║
║   Ethereum + Solana Node Emulator        ║
║   Author: Josué Argaña Silguero          ║
╚══════════════════════════════════════════╝
""")
    
    # Start both honeypots
    eth = N7Honeypot(8545, "ethereum")
    sol = N7Honeypot(8899, "solana")
    
    t1 = threading.Thread(target=eth.start, daemon=True)
    t2 = threading.Thread(target=sol.start, daemon=True)
    
    t1.start()
    t2.start()
    
    print("Honeypots running. Press Ctrl+C to stop.\n")
    print("Port 8545: Ethereum JSON-RPC")
    print("Port 8899: Solana JSON-RPC\n")
    
    try:
        while True:
            time.sleep(5)
            # Quick status
            print(f"  [status] ETH:{len(eth.interactions)} int / SOL:{len(sol.interactions)} int / Wallets:{len(eth.wallets_seen | sol.wallets_seen)}", end='\r')
    except KeyboardInterrupt:
        eth.stop()
        sol.stop()
