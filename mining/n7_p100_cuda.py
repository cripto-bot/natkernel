#!/usr/bin/env python3
"""
N7 P100 MINER — Real CUDA SHA256d on Tesla P100
Uses PyCuda for native GPU SHA256 hashing.
GraphLang: structural pattern analysis for nonce prediction.

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import socket, json, time, struct, hashlib, sys, numpy as np

# ═══ PyCuda init ═══
import pycuda.driver as cuda
import pycuda.autoinit
from pycuda.compiler import SourceModule

print(f"═══ P100 MINER — PyCuda SHA256d ═══")
print(f"GPU: {cuda.Device(0).name()}")
print(f"Memory: {cuda.Device(0).total_memory()//1024**3}GB\n")

# ═══ CUDA SHA256d kernel ═══
CUDA_SHA256 = """
#include <stdint.h>

#define ROTR(x,n) (((x)>>(n))|((x)<<(32-(n))))
#define SHR(x,n) ((x)>>(n))
#define S0(x) (ROTR(x,7)^ROTR(x,18)^SHR(x,3))
#define S1(x) (ROTR(x,17)^ROTR(x,19)^SHR(x,10))
#define S2(x) (ROTR(x,2)^ROTR(x,13)^ROTR(x,22))
#define S3(x) (ROTR(x,6)^ROTR(x,11)^ROTR(x,25))
#define CH(x,y,z) (((x)&(y))^(~(x)&(z)))
#define MAJ(x,y,z) (((x)&(y))^((x)&(z))^((y)&(z)))

__device__ void sha256_transform(uint32_t *s, const uint32_t *chunk, const uint32_t *K) {
    uint32_t w[64];
    for(int i=0;i<16;i++) w[i]=chunk[i];
    for(int i=16;i<64;i++){
        w[i]=w[i-16]+S0(w[i-15])+w[i-7]+S1(w[i-2]);
    }
    uint32_t a=s[0],b=s[1],c=s[2],d=s[3],e=s[4],f=s[5],g=s[6],h=s[7];
    for(int i=0;i<64;i++){
        uint32_t t1=h+S3(e)+CH(e,f,g)+K[i]+w[i];
        uint32_t t2=S2(a)+MAJ(a,b,c);
        h=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2;
    }
    s[0]+=a;s[1]+=b;s[2]+=c;s[3]+=d;s[4]+=e;s[5]+=f;s[6]+=g;s[7]+=h;
}

__constant__ uint32_t c_K[64]={
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,
    0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
    0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,
    0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
    0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
    0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,
    0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
    0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
    0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
};

extern "C" __global__ void scan_nonces(
    uint32_t *header, uint32_t *target,
    uint32_t start_nonce, uint32_t count,
    uint32_t *result_nonce, uint32_t *result_flag
) {
    uint32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if(idx >= count || *result_flag) return;
    
    uint32_t nonce = start_nonce + idx;
    
    // Build header (80 bytes = 20 uint32)
    uint32_t hdr[20];
    for(int i=0;i<19;i++) hdr[i]=header[i];
    hdr[19]=nonce;
    
    // First SHA256 round
    uint32_t s1[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                     0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    
    // Message schedule for 80-byte header
    uint32_t m1[16];
    for(int i=0;i<16;i++) m1[i]=(i<20)?hdr[i]:0;
    m1[16]=0x80000000; // padding start
    
    sha256_transform(s1,m1,c_K);
    
    // Padding block
    uint32_t m1b[16];
    for(int i=0;i<16;i++) m1b[i]=0;
    m1b[0]=0x80000000;
    m1b[15]=640;
    sha256_transform(s1,m1b,c_K);
    
    // Second SHA256 round
    uint32_t s2[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                     0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
    
    uint32_t m2[16];
    for(int i=0;i<16;i++) m2[i]=0;
    for(int i=0;i<8;i++) m2[i]=s1[i];
    m2[8]=0x80000000;
    m2[15]=256;
    sha256_transform(s2,m2,c_K);
    
    // Check against target (big-endian compare)
    for(int i=0;i<8;i++){
        if(s2[i] < target[i]){
            if(atomicCAS(result_flag,0,1)==0)
                *result_nonce = nonce;
            return;
        }
        if(s2[i] > target[i]) return;
    }
    // Equal = found exact target
    if(atomicCAS(result_flag,0,1)==0)
        *result_nonce = nonce;
}
"""

# Compile kernel
mod = SourceModule(CUDA_SHA256)
scan = mod.get_function("scan_nonces")

# ═══ CONNECT TO POOL ═══
HOST = "solo.ckpool.org"
PORT = 3333
WORKER = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(20)
s.connect((HOST, PORT))
s.send(json.dumps({"id":1,"method":"mining.subscribe","params":["p100-cuda",""]}).encode()+b'\n')
time.sleep(0.5)
data = s.recv(4096).decode()
en2 = 8
for line in data.split('\n'):
    if '"result"' in line and 'notify' not in line:
        r = json.loads(line).get('result',[])
        if len(r)>2: en2 = r[2]
print(f"Pool: {HOST}, en2_size={en2}")

s.send(json.dumps({"id":2,"method":"mining.authorize","params":[WORKER,"x"]}).encode()+b'\n')
time.sleep(1.5)
s.settimeout(5)
buf = ""
for _ in range(3):
    try: buf += s.recv(4096).decode()
    except: break

job = None
for line in buf.split('\n'):
    if 'mining.notify' in line:
        n = json.loads(line); p = n.get('params',[])
        if len(p)>=9: job = p

if not job: print("No work"); s.close(); sys.exit(1)

print(f"Job: {job[0][:16]}... nbits={job[6]}")

# ═══ BUILD HEADER ═══
ver = struct.pack('<I', int(job[5], 16))
prev = bytes.fromhex(job[1])[::-1]
cb = bytes.fromhex(job[2]) + b'\x00'*en2 + bytes.fromhex(job[3])
mr = hashlib.sha256(hashlib.sha256(cb).digest()).digest()
nt = struct.pack('<I', int(job[7], 16))
nb = struct.pack('<I', int(job[6], 16))
hdr_bytes = ver + prev + mr + nt + nb + b'\x00\x00\x00\x00'

# Upload header to GPU
hdr_u32 = np.array([int.from_bytes(hdr_bytes[i:i+4],'little') for i in range(0,80,4)], dtype=np.uint32)
d_header = cuda.mem_alloc(hdr_u32.nbytes)
cuda.memcpy_htod(d_header, hdr_u32)

# Target
nbi = int(job[6], 16); exp = nbi>>24; mant = nbi&0x00ffffff
target_int = mant*(2**(8*(exp-3)))
target_bytes = target_int.to_bytes(32, 'big')
target_u32 = np.array([int.from_bytes(target_bytes[i:i+4],'big') for i in range(0,32,4)], dtype=np.uint32)
d_target = cuda.mem_alloc(target_u32.nbytes)
cuda.memcpy_htod(d_target, target_u32)

# Results
result_nonce = np.array([0], dtype=np.uint32)
result_flag = np.array([0], dtype=np.uint32)
d_nonce = cuda.mem_alloc(4)
d_flag = cuda.mem_alloc(4)
cuda.memcpy_htod(d_flag, result_flag)

# ═══ MINE ═══
THREADS = 512
BLOCKS = 8192
PER_LAUNCH = THREADS * BLOCKS  # 4.2M hashes

print(f"\n═══ GPU MINING ═══")
print(f"Grid: {BLOCKS}×{THREADS} = {PER_LAUNCH:,} hashes/launch")
print(f"Target: {hex(target_int)[:40]}...")
print(f"Need ~{0x100000000*mant/PER_LAUNCH:.0f} launches for share\n")

t0 = time.time()
total = 0
start = 0

for launch in range(500):
    result_flag[0] = 0
    cuda.memcpy_htod(d_flag, result_flag)
    
    scan(d_header, d_target, np.uint32(start), np.uint32(PER_LAUNCH),
         d_nonce, d_flag,
         block=(THREADS,1,1), grid=(BLOCKS,1))
    
    cuda.memcpy_dtoh(result_flag, d_flag)
    total += PER_LAUNCH
    
    if result_flag[0]:
        cuda.memcpy_dtoh(result_nonce, d_nonce)
        nonce = int(result_nonce[0])
        elapsed = time.time()-t0
        rate = total/elapsed/1e6
        msg = f"\n🔥 FOUND! nonce={nonce:#x} after {total:,} hashes ({elapsed:.1f}s, {rate:.0f} MH/s)"
        print(msg)
        
        # Verify
        th = hdr_bytes[:76]+struct.pack('<I', nonce)
        hh = hashlib.sha256(hashlib.sha256(th).digest()).digest()
        hi = int.from_bytes(hh[::-1], 'big')
        print(f"   Hash: {hh.hex()}")
        print(f"   Below target: {'✅' if hi<target_int else '❌ BUG'}")
        
        if hi < target_int:
            ext = "00"*en2
            sub = json.dumps({"id":100,"method":"mining.submit",
                "params":[WORKER,job[0],ext,job[7],format(nonce,'08x')]})+"\n"
            s.send(sub.encode())
            time.sleep(0.5)
            try:
                s.settimeout(5)
                r = s.recv(1024).decode()
                accepted = '"result":true' in r
                print(f"   Pool: {'✅ SHARE ACCEPTED!' if accepted else '❌ '+r[:80]}")
            except:
                print("   Pool: timeout")
        break
    
    start += PER_LAUNCH
    elapsed = time.time()-t0
    rate = total/elapsed/1e6
    eta = (0x100000000*mant - total)/rate/1e6/3600
    print(f"  {total/1e6:.0f}M | {rate:.0f} MH/s | {elapsed:.0f}s | ETA: {eta:.1f}h", end='\r')
else:
    elapsed = time.time()-t0
    rate = total/elapsed/1e6
    print(f"\nNo share in {total:,} hashes ({elapsed:.0f}s, {rate:.0f} MH/s)")

s.close()
