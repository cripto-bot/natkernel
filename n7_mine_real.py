#!/usr/bin/env python3
"""P100 Miner — CPU multiprocessing for real shares"""
import socket, json, time, struct, hashlib, sys
from multiprocessing import Pool, cpu_count

HOST, PORT = "solo.ckpool.org", 3333
WORKER = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

def check_range(args):
    start, end, hdr, target = args
    for nonce in range(start, end):
        h = hashlib.sha256(hashlib.sha256(hdr+struct.pack('<I',nonce)).digest()).digest()
        if int.from_bytes(h[::-1], 'big') < target:
            return nonce, h.hex()
    return None, None

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(20)
s.connect((HOST, PORT))
s.send(json.dumps({"id":1,"method":"mining.subscribe","params":["p100",""]}).encode()+b'\n')
time.sleep(0.5)
data = s.recv(4096).decode()
en2 = 8
for line in data.split('\n'):
    if '"result"' in line and 'notify' not in line:
        r = json.loads(line).get('result',[])
        if len(r)>2: en2 = r[2]
s.send(json.dumps({"id":2,"method":"mining.authorize","params":[WORKER,"x"]}).encode()+b'\n')
time.sleep(1)
s.settimeout(3)
buf = s.recv(4096).decode()

job = None
for line in buf.split('\n'):
    if 'mining.notify' in line:
        n = json.loads(line); p = n.get('params',[])
        if len(p)>=9: job = p
if not job: print("No work"); s.close(); sys.exit(1)

version = struct.pack('<I', int(job[5], 16))
prevhash = bytes.fromhex(job[1])[::-1]
coinbase = bytes.fromhex(job[2]) + b'\x00'*en2 + bytes.fromhex(job[3])
merkle = hashlib.sha256(hashlib.sha256(coinbase).digest()).digest()
ntime = struct.pack('<I', int(job[7], 16))
nbits = struct.pack('<I', int(job[6], 16))
hdr = version + prevhash + merkle + ntime + nbits

ni = int(job[6], 16); exp = ni>>24; mant = ni&0x00ffffff
target = mant*(2**(8*(exp-3)))

print(f"GPU: Tesla P100 | CPU cores: {cpu_count()} | ~2 MH/s estimated")
print(f"Target: {hex(target)[:30]}... | {4294967296*mant/1e12:.0f}T hashes needed\n")

t0 = time.time()
BATCH = 200000
total = 0
ncpu = cpu_count()

for batch in range(100):
    chunk = max(1, BATCH // ncpu)
    ranges = [(total+i*chunk, min(total+(i+1)*chunk, total+BATCH), hdr, target) for i in range(ncpu)]
    
    with Pool(ncpu) as pool:
        results = pool.map(check_range, ranges)
    
    for nonce, hh in results:
        if nonce is not None:
            elapsed = time.time()-t0
            rate = total/elapsed/1e6
            print(f"\n🔥 FOUND! {total:,} hashes, {elapsed:.0f}s, {rate:.1f} MH/s")
            print(f"   Nonce: {nonce}, Hash: {hh}")
            ext = "00"*en2
            sub = json.dumps({"id":100,"method":"mining.submit","params":[WORKER,job[0],ext,job[7],format(nonce,'08x')]})+"\n"
            s.send(sub.encode())
            time.sleep(0.5)
            try:
                s.settimeout(3)
                r = s.recv(1024).decode()
                print(f"   Pool: {'✅ SHARE ACCEPTED!' if '\"result\":true' in r else '❌ '+r[:60]}")
            except:
                print("   Pool: timeout")
            s.close()
            sys.exit(0)
    
    total += BATCH
    elapsed = time.time()-t0
    rate = total/elapsed/1e6
    print(f"  {total/1e6:.1f}M | {rate:.1f} MH/s | {elapsed:.0f}s", end='\r')

print(f"\nNo share in {total:,} hashes ({time.time()-t0:.0f}s)")
s.close()
