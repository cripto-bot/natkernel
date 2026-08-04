#!/usr/bin/env python3
"""P100 Bitcoin Miner — Real GPU SHA256"""
import socket, json, time, struct, hashlib, sys
import numpy as np
import cupy as cp

HOST = "solo.ckpool.org"
PORT = 3333
WORKER = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

# Load CUDA
ptx = open('/tmp/sha256.ptx').read()
mod = cp.RawModule(code=ptx)
mine_kernel = mod.get_function('bitcoin_mine')

print(f"GPU: {cp.cuda.Device().name()}\n")

# Connect
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(20)
s.connect((HOST, PORT))
s.send(json.dumps({"id":1,"method":"mining.subscribe","params":["p100",""]}).encode()+b'\n')
time.sleep(0.5)
data = s.recv(4096).decode()
for line in data.split('\n'):
    if '"result"' in line and 'notify' not in line:
        r = json.loads(line).get('result',[])
        en2_size = r[2] if len(r)>2 else 8
print(f"en2_size: {en2_size}")

s.send(json.dumps({"id":2,"method":"mining.authorize","params":[WORKER,"x"]}).encode()+b'\n')
time.sleep(1)
s.settimeout(5)
buf = s.recv(4096).decode()

job = None
for line in buf.split('\n'):
    if 'mining.notify' in line:
        n = json.loads(line); p = n.get('params',[])
        if len(p)>=9: job = p

if not job:
    print("No work"); s.close(); sys.exit(1)

print(f"Job: {job[0][:16]}... nbits={job[6]}")

# Build header
version = struct.pack('<I', int(job[5], 16))
prevhash = bytes.fromhex(job[1])[::-1]
coinbase = bytes.fromhex(job[2]) + b'\x00'*en2_size + bytes.fromhex(job[3])
merkle = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()
ntime = struct.pack('<I', int(job[7], 16))
nbits = struct.pack('<I', int(job[6], 16))
header = version + prevhash + merkle + ntime + nbits + b'\x00\x00\x00\x00'

hdr_u32 = cp.array([int.from_bytes(header[i:i+4],'little') for i in range(0,80,4)], dtype=cp.uint32)

# Target
nbits_int = int(job[6], 16)
exp = nbits_int >> 24; mant = nbits_int & 0x00ffffff
target_int = mant * (2**(8*(exp-3)))
target_bytes = target_int.to_bytes(32, 'big')
target_u32 = cp.array([int.from_bytes(target_bytes[i:i+4],'big') for i in range(0,32,4)], dtype=cp.uint32)

found_nonce = cp.array([0], dtype=cp.uint32)
found_flag = cp.array([0], dtype=cp.uint32)

# Mine
THREADS, BLOCKS = 256, 16384
BATCH = THREADS * BLOCKS
print(f"Launch: {BLOCKS}×{THREADS}={BATCH:,} hashes/launch")
print(f"Target: {hex(target_int)[:40]}...\n")

t0 = time.time()
total = 0
start = 0

for b in range(100):
    found_flag[0] = 0
    mine_kernel((BLOCKS,),(THREADS,),(hdr_u32, target_u32, start, BATCH, found_nonce, found_flag))
    cp.cuda.Stream.null.synchronize()
    total += BATCH
    
    if found_flag[0]:
        nonce = int(found_nonce[0])
        elapsed = time.time()-t0
        rate = total/elapsed/1e6
        print(f"\n🔥 FOUND nonce={nonce:#x} after {total:,} hashes ({elapsed:.1f}s, {rate:.1f} MH/s)")
        
        # Verify
        test = header[:76]+struct.pack('<I', nonce)
        h = hashlib.sha256(hashlib.sha256(test).digest()).digest()
        h_int = int.from_bytes(h[::-1], 'big')
        valid = h_int < target_int
        print(f"   Valid: {'✅' if valid else '❌ BUG'} | Hash: {h.hex()[:32]}...")
        
        if valid:
            ext = "00"*en2_size
            submit = json.dumps({"id":100,"method":"mining.submit","params":[WORKER,job[0],ext,job[7],format(nonce,'08x')]})+"\n"
            s.send(submit.encode())
            time.sleep(0.5)
            try:
                s.settimeout(3)
                resp = s.recv(1024).decode()
                print(f"   Pool: {'✅ ACCEPTED!' if '\"result\":true' in resp else '❌ '+resp[:60]}")
            except:
                print("   Pool: timeout")
        break
    
    start += BATCH
    elapsed = time.time()-t0
    rate = total/elapsed/1e6 if elapsed>0 else 0
    print(f"  {total/1e6:.0f}M hashes, {rate:.1f} MH/s, {elapsed:.0f}s", end='\r')

else:
    elapsed = time.time()-t0
    rate = total/elapsed/1e6
    print(f"\nNo share in {total:,} ({elapsed:.0f}s, {rate:.1f} MH/s)")
    print(f"Diff {nbits_int&0x00ffffff} × 2^{exp-3} = need ~{4294967296*(nbits_int&0x00ffffff)/total:.0f}x more")

s.close()
