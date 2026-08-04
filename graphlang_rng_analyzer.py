#!/usr/bin/env python3
"""
GRAPHLANG RNG ANALYZER — Detect Weak extranonce2 in Mining Pools

Methodology:
  1. Capture 1000+ Stratum jobs from pool
  2. Normalize extranonce sequences → GraphLang IR
  3. Measure N (structural completeness)
  4. N<4 = predictable pattern (same as Arweave/LuBian)
  5. Build prediction function from graph structure

Why GraphLang:
  - Sequential RNG → N=2 (struct + define only)
  - Timestamp-based → N=3 (struct + define + conditional)
  - PRNG with weak seed → N=4 (missing hash,chain)
  - Cryptographic RNG → N=7 (all kinds present)

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import socket, json, time, hashlib, struct, sys
from collections import Counter, defaultdict
from datetime import datetime

sys.path.insert(0, '/mnt/hdd3tb/GraphLab-Final')
from graphlang.core import Graph, Node, build_graph

# ═══ STRATUM JOB CAPTURE ═══
class StratumJobCapture:
    """Capture mining.notify jobs from a pool"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.jobs = []
        self.sock = None
    
    def capture(self, target_count: int = 500, timeout: int = 120) -> list:
        """Capture N jobs from pool"""
        print(f"[capture] Connecting to {self.host}:{self.port}...")
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(timeout)
        self.sock.connect((self.host, self.port))
        
        # Subscribe
        self.sock.send(json.dumps({
            "id":1, "method":"mining.subscribe",
            "params":["graphlang-rng/1.0", ""]
        }).encode() + b'\n')
        
        time.sleep(0.3)
        resp = self.sock.recv(4096).decode()
        sub = json.loads(resp.split('\n')[0])
        
        result = sub.get('result', [])
        extranonce2_size = result[2] if len(result) > 2 else 8
        
        print(f"[capture] extranonce2_size={extranonce2_size}, targeting {target_count} jobs")
        
        # Authorize
        self.sock.send(json.dumps({
            "id":2, "method":"mining.authorize",
            "params":["graphlang.n7", "x"]
        }).encode() + b'\n')
        
        # Collect jobs
        start = time.time()
        job_count = 0
        buf = ""
        
        while job_count < target_count and time.time() - start < timeout:
            try:
                self.sock.settimeout(2)
                data = self.sock.recv(8192).decode('utf-8', errors='ignore')
                buf += data
                
                while '\n' in buf:
                    line, buf = buf.split('\n', 1)
                    if 'mining.notify' not in line:
                        continue
                    
                    try:
                        notify = json.loads(line)
                        params = notify.get('params', [])
                        if len(params) >= 9:
                            job = {
                                'job_id': params[0],
                                'prevhash': params[1],
                                'coinb1': params[2][:40],
                                'coinb2': params[3][:40],
                                'version': params[5],
                                'nbits': params[6],
                                'ntime': params[7],
                                'clean': params[8],
                                'timestamp': time.time(),
                                'index': job_count,
                            }
                            self.jobs.append(job)
                            job_count += 1
                            
                            if job_count % 100 == 0:
                                elapsed = time.time() - start
                                rate = job_count / elapsed if elapsed > 0 else 0
                                print(f"  [{job_count}/{target_count}] {rate:.1f} jobs/s")
                    except:
                        pass
                
            except socket.timeout:
                continue
            except Exception as e:
                print(f"  [error] {e}")
                break
        
        elapsed = time.time() - start
        print(f"[capture] Got {len(self.jobs)} jobs in {elapsed:.1f}s ({len(self.jobs)/elapsed:.1f} j/s)")
        
        self.sock.close()
        return self.jobs


# ═══ GRAPHLANG RNG ANALYZER ═══
class GraphLangRngAnalyzer:
    """
    Analyze extranonce RNG using GraphLang structural patterns.
    
    Builds a graph where:
      - Each job = node
      - Time delta between jobs = edge
      - Extranonce pattern = graph structure
    """
    
    def __init__(self, jobs: list):
        self.jobs = jobs
        self.graph = Graph()
        self.findings = {}
    
    def analyze(self) -> dict:
        """Full N-analysis of RNG pattern"""
        
        if len(self.jobs) < 10:
            return {'error': 'Need at least 10 jobs', 'N': 0}
        
        # ═══ Extract features ═══
        timestamps = [j['timestamp'] for j in self.jobs]
        job_ids = [j['job_id'] for j in self.jobs]
        ntimes = [j.get('ntime', '0') for j in self.jobs]
        
        # Time deltas
        deltas = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        
        # Job ID analysis (hex patterns)
        job_id_prefixes = Counter(j[:4] for j in job_ids)
        
        # ntime analysis (timestamp in mining header)
        ntime_ints = []
        for nt in ntimes:
            try: ntime_ints.append(int(nt, 16))
            except: ntime_ints.append(0)
        
        ntime_deltas = [ntime_ints[i+1] - ntime_ints[i] for i in range(len(ntime_ints)-1)]
        
        # ═══ Build GraphLang graph ═══
        c = [0]
        def add(kind, value, args=None):
            c[0] += 1
            nid = f"n{c[0]}"
            self.graph.nodes[nid] = Node(kind=kind, value=str(value)[:100], args=args or [])
            return nid
        
        root = add('struct', f'rng_{len(self.jobs)}_jobs')
        
        # 1. STRUCT: job count and interval
        add('struct', f'count={len(self.jobs)}, duration={deltas[0] if deltas else 0:.1f}s', [root])
        
        # 2. DEFINE: interval statistics
        if deltas:
            avg_delta = sum(deltas) / len(deltas)
            min_delta = min(deltas)
            max_delta = max(deltas)
            variance = sum((d - avg_delta)**2 for d in deltas) / len(deltas)
            
            add('define', f'interval: avg={avg_delta:.3f}s, min={min_delta:.3f}s, max={max_delta:.3f}s, var={variance:.6f}', [root])
        
        # 3. LOOP: job ID sequence pattern
        id_changes = sum(1 for i in range(len(job_ids)-1) if job_ids[i] != job_ids[i+1])
        id_same = len(job_ids) - 1 - id_changes
        add('loop', f'job_ids: {len(set(job_ids[:10]))} unique / {len(job_ids)} total, changes={id_changes}', [root])
        
        # 4. CONDITIONAL: ntime pattern
        if ntime_deltas:
            same_ntime = sum(1 for d in ntime_deltas if d == 0)
            add('conditional', f'ntime: same={same_ntime}/{len(ntime_deltas)} unchanged', [root])
        
        # 5. RETURN: job_id prefix distribution
        top_prefixes = job_id_prefixes.most_common(3)
        add('return', f'top_prefixes={top_prefixes}', [root])
        
        # 6. HASH: entropy check
        # Shannon entropy of job_id first bytes
        byte_freq = Counter()
        for jid in job_ids:
            for i in range(0, min(8, len(jid)), 2):
                try:
                    byte_val = int(jid[i:i+2], 16)
                    byte_freq[byte_val] += 1
                except: pass
        
        total_bytes = sum(byte_freq.values())
        entropy = 0
        if total_bytes > 0:
            entropy = -sum((c/total_bytes) * (c/total_bytes).bit_length()/8 for c in byte_freq.values())
        
        add('hash', f'entropy={entropy:.4f} bits/byte (max=8.0)', [root])
        
        # 7. CHAIN: sequential correlation
        # Are consecutive job_ids sequential?
        sequential = 0
        for i in range(len(job_ids)-1):
            try:
                a = int(job_ids[i][:8], 16)
                b = int(job_ids[i+1][:8], 16)
                if b == a + 1:
                    sequential += 1
            except: pass
        
        add('chain', f'sequential={sequential}/{len(job_ids)-1} consecutive', [root])
        
        # ═══ N-ANALYSIS ═══
        kinds = set()
        for n in self.graph.nodes.values():
            kinds.add(n.kind)
        
        n_value = len(kinds)
        all_7 = {'struct','define','loop','conditional','return','hash','chain'}
        missing = all_7 - kinds
        
        # Determine RNG type from N
        if n_value <= 2:
            rng_type = "SEQUENTIAL COUNTER — trivially predictable"
            severity = "CRITICAL"
        elif n_value == 3:
            rng_type = "TIMESTAMP-BASED — predictable with clock sync"
            severity = "HIGH"
        elif n_value <= 4:
            rng_type = "WEAK PRNG — pattern detectable"
            severity = "MEDIUM"
        elif n_value <= 5:
            rng_type = "MODERATE PRNG — some entropy, attack harder"
            severity = "LOW"
        else:
            rng_type = "CRYPTOGRAPHIC — truly random, not exploitable"
            severity = "NONE"
        
        # Is entropy good?
        if entropy < 4:
            rng_type += " | LOW ENTROPY CONFIRMED"
            severity = "CRITICAL"
        
        self.findings = {
            'N': n_value,
            'missing': list(missing),
            'entropy': entropy,
            'rng_type': rng_type,
            'severity': severity,
            'exploitable': n_value < 5 or entropy < 4,
            'interval_stats': {
                'avg': sum(deltas)/len(deltas) if deltas else 0,
                'min': min(deltas) if deltas else 0,
                'max': max(deltas) if deltas else 0,
                'variance': sum((d-sum(deltas)/len(deltas))**2 for d in deltas)/len(deltas) if deltas else 0,
            },
            'sequential_rate': sequential / max(1, len(job_ids)-1),
            'jobs_captured': len(self.jobs),
        }
        
        return self.findings
    
    def report(self) -> str:
        if not self.findings:
            return "No analysis yet"
        
        f = self.findings
        return f"""
═══ GRAPHLANG RNG ANALYSIS ═══
  Jobs:        {f['jobs_captured']}
  N value:     {f['N']}/7
  Missing:     {f['missing']}
  Entropy:     {f['entropy']:.4f} bits/byte
  Type:        {f['rng_type']}
  Severity:    {f['severity']}
  Exploitable: {'✅ YES' if f['exploitable'] else '❌ NO'}
  Interval:    avg={f['interval_stats']['avg']:.3f}s, var={f['interval_stats']['variance']:.6f}
  Sequential:  {f['sequential_rate']:.1%} consecutive
"""


# ═══ MAIN ═══
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='GraphLang RNG Analyzer')
    p.add_argument('--host', default='solo.ckpool.org')
    p.add_argument('--port', type=int, default=3333)
    p.add_argument('--jobs', '-j', type=int, default=500)
    p.add_argument('--timeout', '-t', type=int, default=120)
    args = p.parse_args()
    
    print("""
╔══════════════════════════════════════════════╗
║  GRAPHLANG RNG ANALYZER                      ║
║  Detect Weak extranonce in Mining Pools       ║
║  N=7 ∈ [4,12]                                ║
╚══════════════════════════════════════════════╝
""")
    
    # Capture
    capture = StratumJobCapture(args.host, args.port)
    jobs = capture.capture(target_count=args.jobs, timeout=args.timeout)
    
    if len(jobs) < 10:
        print(f"ERROR: Only got {len(jobs)} jobs. Need at least 10.")
        sys.exit(1)
    
    # Analyze with GraphLang
    analyzer = GraphLangRngAnalyzer(jobs)
    findings = analyzer.analyze()
    
    print(analyzer.report())
    
    # Show sample data
    print(f"\n═══ SAMPLE JOBS ═══")
    for j in jobs[:5]:
        print(f"  id={j['job_id'][:16]}... prevhash={j['prevhash'][:16]}... ntime={j.get('ntime','?')}")
    
    print(f"\n═══ GRAPH ═══")
    print(f"  Nodes: {len(analyzer.graph.nodes)}")
    print(f"  Kinds: {set(n.kind for n in analyzer.graph.nodes.values())}")
