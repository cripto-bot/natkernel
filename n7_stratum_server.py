#!/usr/bin/env python3
"""
N7 STRATUM SERVER — Local pool with configurable difficulty
For PoC: P100 mining → find share → submit → accepted

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import socket, json, struct, hashlib, random, threading, time, sys
from datetime import datetime

# ═══ CONFIG ═══
HOST = "127.0.0.1"
PORT = 3333
DIFFICULTY = 1  # Very low — share every ~4 min at 296 MH/s

class N7StratumServer:
    def __init__(self, host=HOST, port=PORT, difficulty=DIFFICULTY):
        self.host = host
        self.port = port
        self.difficulty = difficulty
        self.sessions = {}
        self.job_id_counter = 0
        
        # Generate a "block template" for mining
        self._new_block()
    
    def _new_block(self):
        """Generate new block template"""
        self.job_id_counter += 1
        self.job_id = format(self.job_id_counter, '016x')
        
        # Use Bitcoin mainnet genesis block as template (modified)
        self.version = "20000000"
        # Previous hash — use random for testing
        self.prevhash = hashlib.sha256(str(time.time()).encode()).hexdigest()
        # Coinbase parts
        self.coinb1 = "01000000010000000000000000000000000000000000000000000000000000000000000000ffffffff2003"
        self.coinb2 = "0d2f6e6f64655374726174756d2f00000000020000000000000000266a24aa21a9ed000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000002a0000000000000000266a24aa21a9ed00000000000000000000000000000000000000000000000000000000000000000000000000"
        self.merkle_branches = []
        self.ntime = format(int(time.time()), '08x')
        self.nbits = "207fffff"  # Very low difficulty (~1)
        self.clean_jobs = True
        
        # Calculate target from nbits
        nbits_int = int(self.nbits, 16)
        exp = nbits_int >> 24
        mant = nbits_int & 0x00ffffff
        self.target = mant * (2 ** (8 * (exp - 3)))
        
        self.extranonce1 = format(random.randint(0, 0xFFFFFFFF), '08x')
        self.extranonce2_size = 8
    
    def _verify_share(self, worker, job_id, extranonce2_hex, ntime_hex, nonce_hex) -> bool:
        """Verify if a share meets the difficulty target"""
        # Build header
        ver = bytes.fromhex(self.version)[::-1]
        prev = bytes.fromhex(self.prevhash)[::-1]
        coinbase = bytes.fromhex(self.coinb1) + bytes.fromhex(extranonce2_hex) + bytes.fromhex(self.coinb2)
        mr = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()
        nt = bytes.fromhex(ntime_hex)[::-1]
        nb = bytes.fromhex(self.nbits)[::-1]
        nonce = bytes.fromhex(nonce_hex)[::-1]
        header = ver + prev + mr + nt + nb + nonce
        
        h = hashlib.sha256(hashlib.sha256(header).digest()).digest()
        hash_int = int.from_bytes(h[::-1], 'big')
        
        return hash_int < self.target
    
    def _handle_client(self, client_sock, addr):
        """Handle one Stratum client"""
        session = {
            'subscribed': False,
            'authorized': False,
            'worker': '',
            'extranonce1': self.extranonce1,
            'extranonce2_size': self.extranonce2_size,
        }
        
        buf = ""
        
        try:
            while True:
                data = client_sock.recv(4096).decode('utf-8', errors='ignore')
                if not data: break
                buf += data
                
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    if not line.strip(): continue
                    
                    try:
                        msg = json.loads(line)
                    except:
                        continue
                    
                    method = msg.get('method', '')
                    msg_id = msg.get('id', 0)
                    params = msg.get('params', [])
                    
                    if method == 'mining.subscribe':
                        response = json.dumps({
                            "id": msg_id,
                            "result": [
                                [["mining.set_difficulty", str(self.difficulty)],
                                 ["mining.notify", self.job_id]],
                                self.extranonce1,
                                self.extranonce2_size
                            ],
                            "error": None
                        }) + "\n"
                        client_sock.send(response.encode())
                        session['subscribed'] = True
                        
                        # Send difficulty
                        diff_msg = json.dumps({
                            "id": None,
                            "method": "mining.set_difficulty",
                            "params": [self.difficulty]
                        }) + "\n"
                        client_sock.send(diff_msg.encode())
                        
                        print(f"[{addr[0]}:{addr[1]}] subscribed, diff={self.difficulty}")
                    
                    elif method == 'mining.authorize':
                        worker = params[0] if params else 'unknown'
                        session['worker'] = worker
                        session['authorized'] = True
                        
                        response = json.dumps({
                            "id": msg_id,
                            "result": True,
                            "error": None
                        }) + "\n"
                        client_sock.send(response.encode())
                        
                        print(f"[{addr[0]}:{addr[1]}] authorized: {worker}")
                        
                        # Send work immediately
                        self._send_work(client_sock, session)
                    
                    elif method == 'mining.submit':
                        worker_name = params[0] if len(params) > 0 else ''
                        job_id = params[1] if len(params) > 1 else ''
                        extranonce2 = params[2] if len(params) > 2 else ''
                        ntime = params[3] if len(params) > 3 else ''
                        nonce = params[4] if len(params) > 4 else ''
                        
                        valid = self._verify_share(worker_name, job_id, extranonce2, ntime, nonce)
                        
                        if valid:
                            response = json.dumps({
                                "id": msg_id,
                                "result": True,
                                "error": None
                            }) + "\n"
                            print(f"\n{'='*60}")
                            print(f"🔥 SHARE ACCEPTED!")
                            print(f"   Worker: {worker_name[:20]}")
                            print(f"   Nonce:  {nonce}")
                            print(f"   EN2:    {extranonce2}")
                            print(f"   Diff:   {self.difficulty}")
                            print(f"{'='*60}\n")
                        else:
                            response = json.dumps({
                                "id": msg_id,
                                "result": None,
                                "error": [23, "Share below target", None]
                            }) + "\n"
                        
                        client_sock.send(response.encode())
                        
                        if valid:
                            # Send new work
                            self._new_block()
                            self._send_work(client_sock, session)
        
        except Exception as e:
            print(f"[{addr}] Error: {e}")
        finally:
            client_sock.close()
    
    def _send_work(self, client_sock, session):
        """Send mining.notify with work"""
        notify = json.dumps({
            "id": None,
            "method": "mining.notify",
            "params": [
                self.job_id,
                self.prevhash,
                self.coinb1,
                self.coinb2,
                self.merkle_branches,
                self.version,
                self.nbits,
                self.ntime,
                self.clean_jobs
            ]
        }) + "\n"
        client_sock.send(notify.encode())
        print(f"[work] job={self.job_id[:12]}, nbits={self.nbits}, diff={self.difficulty}")
    
    def start(self):
        """Start stratum server"""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(5)
        
        print(f"""
╔══════════════════════════════════════════════╗
║  N7 STRATUM SERVER                           ║
║  Local pool for PoC                          ║
╚══════════════════════════════════════════════╝
  Listening: {self.host}:{self.port}
  Difficulty: {self.difficulty} (very low — easy shares)
  Target:    {hex(self.target)[:30]}...
  Wait:      1 share every ~4 min at 296 MH/s
  
  Connect:   stratum+tcp://{self.host}:{self.port}
""")
        
        while True:
            client, addr = server.accept()
            thread = threading.Thread(target=self._handle_client, args=(client, addr), daemon=True)
            thread.start()


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--port', '-p', type=int, default=3333)
    p.add_argument('--diff', '-d', type=int, default=1, help='Difficulty (1=very easy)')
    args = p.parse_args()
    
    server = N7StratumServer(difficulty=args.diff, port=args.port)
    server.start()
