#!/usr/bin/env python3
"""
GRAPHLANG ON-CHAIN TRACER — Wallet Network Mapper

Uses GraphLang core to build a structural graph of wallet relationships.
Every wallet = node, every transaction = edge, every token = property.

N=7 structural analysis applied to blockchain forensics:
  1. struct    → wallet identity
  2. define    → SOL/token balances
  3. loop      → transaction iteration
  4. conditional → fund flow direction (in/out)
  5. return    → counterparty discovery
  6. hash      → transaction signatures
  7. chain     → wallet→wallet link building

The trace IS a GraphLang graph. Not a script — a structure.

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import urllib.request, json, time, sys, os
from pathlib import Path

sys.path.insert(0, '/mnt/hdd3tb/GraphLab-Final')
from graphlang.core import Graph, Node, build_graph, graph_to_json

RPC = "https://api.mainnet-beta.solana.com"

def rpc(method, params):
    p = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params})
    r = urllib.request.Request(RPC, data=p.encode(),
        headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(r, timeout=10) as resp:
        return json.loads(resp.read()).get('result',{})


class GraphLangTracer:
    """
    Blockchain tracer powered by GraphLang.
    Every discovery becomes a node in the trace graph.
    """
    
    def __init__(self, seed_wallet: str):
        self.seed = seed_wallet
        self.graph = Graph()
        self.counter = [0]
        
        # Root: the seed wallet
        c = self.counter
        c[0] += 1
        root_id = f"w{c[0]}"
        self.graph.nodes[root_id] = Node(kind='struct', value=seed_wallet[:16])
        self.graph.root = root_id
        self.wallet_nodes = {seed_wallet: root_id}
        
        print(f"[GraphLang] Root: {root_id} = {seed_wallet[:20]}...")
    
    def _add_wallet(self, addr: str, sol_balance: float, parent_id: str = None) -> str:
        """Add wallet node to graph"""
        if addr in self.wallet_nodes:
            return self.wallet_nodes[addr]
        
        self.counter[0] += 1
        nid = f"w{self.counter[0]}"
        
        usd = sol_balance * 150
        size = 'whale' if usd > 50000 else 'large' if usd > 5000 else 'medium' if usd > 500 else 'small'
        
        self.graph.nodes[nid] = Node(
            kind='define',
            value=f"{addr[:16]}...|{sol_balance:.2f}SOL|${usd:.0f}",
            op=size,
            args=[parent_id] if parent_id else []
        )
        
        if parent_id and parent_id in self.graph.nodes:
            self.graph.nodes[parent_id].args.append(nid)
            self.graph.edges.append((parent_id, nid, 'connected_to'))
        
        self.wallet_nodes[addr] = nid
        return nid
    
    def _add_tx_edge(self, from_id: str, to_id: str, signature: str, amount: float):
        """Add transaction edge between wallets"""
        self.counter[0] += 1
        tx_id = f"tx{self.counter[0]}"
        
        self.graph.nodes[tx_id] = Node(
            kind='chain',
            value=f"{signature[:12]}...|{amount:.4f}SOL",
            op='transfer',
            args=[from_id, to_id]
        )
        self.graph.edges.append((from_id, tx_id, 'sent'))
        self.graph.edges.append((tx_id, to_id, 'received'))
    
    def trace(self, depth: int = 2, max_wallets: int = 20):
        """
        Trace wallet network using GraphLang structural graph.
        
        depth: how many hops from seed wallet
        max_wallets: max wallets to discover per hop
        """
        print(f"\n═══ GRAPHLANG TRACE (depth={depth}) ═══\n")
        
        to_process = [(self.seed, 0, self.wallet_nodes[self.seed])]
        processed = set()
        
        while to_process:
            addr, current_depth, parent_id = to_process.pop(0)
            if addr in processed: continue
            if current_depth >= depth: continue
            processed.add(addr)
            
            # Get wallet info — VERIFY EXISTENCE FIRST
            acc = rpc("getAccountInfo", [addr, {"encoding":"jsonParsed"}])
            val = acc.get('value')
            
            if not val:  # Account doesn't exist — skip
                print(f"{prefix}  ⊘ {addr[:20]}... EPHEMERAL (already closed)")
                continue
            
            sol = val.get('lamports',0)/1e9
            
            usd_tag = f"${sol*150:,.0f}"
            nid = self._add_wallet(addr, sol, parent_id)
            
            prefix = "  " * current_depth
            print(f"{prefix}[depth {current_depth}] {addr[:20]}... = {sol:.2f} SOL ({usd_tag})")
            
            if current_depth >= depth - 1:
                continue
            
            # Get transactions
            time.sleep(0.2)
            sigs = rpc("getSignaturesForAddress", [addr, {"limit":5}])
            
            counterparties_found = 0
            for s in sigs[:5]:
                if counterparties_found >= max_wallets // (current_depth + 1):
                    break
                
                time.sleep(0.1)
                tx = rpc("getTransaction", [s['signature'], {"encoding":"jsonParsed","maxSupportedTransactionVersion":0}])
                if not tx: continue
                
                msg = tx.get('transaction',{}).get('message',{})
                meta = tx.get('meta',{})
                accts = msg.get('accountKeys',[])
                
                # Find counterparties (other signers, large balance changes)
                for i, a in enumerate(accts):
                    pk = a['pubkey']
                    if pk == addr or len(pk) < 30: continue
                    if pk in self.wallet_nodes: continue
                    
                    # Check if this counterparty had significant interaction
                    if i < len(meta.get('preBalances',[])):
                        diff = (meta['postBalances'][i] - meta['preBalances'][i]) / 1e9
                        if abs(diff) > 0.01:
                            # Add to processing queue
                            cp_nid = self._add_wallet(pk, 0, nid)
                            self._add_tx_edge(nid, cp_nid, s['signature'], diff)
                            to_process.append((pk, current_depth + 1, cp_nid))
                            counterparties_found += 1
                            
                            print(f"{prefix}  → {pk[:20]}... Δ{diff:+.4f} SOL")
        
        return self.graph
    
    def stats(self) -> dict:
        """Get graph statistics"""
        kinds = {}
        total_sol = 0
        whales = 0
        
        for nid, node in self.graph.nodes.items():
            kinds[node.kind] = kinds.get(node.kind, 0) + 1
            
            if node.kind == 'define':
                parts = node.value.split('|')
                if len(parts) >= 2:
                    try:
                        sol_val = float(parts[1].replace('SOL',''))
                        total_sol += sol_val
                        if sol_val * 150 > 5000:
                            whales += 1
                    except: pass
        
        return {
            'nodes': len(self.graph.nodes),
            'edges': len(self.graph.edges),
            'wallets': kinds.get('define', 0) + kinds.get('struct', 0),
            'transactions': kinds.get('chain', 0),
            'ir_kinds': len(kinds),
            'total_sol_discovered': total_sol,
            'total_usd': total_sol * 150,
            'whales_found': whales,
            'n_value': len(kinds),
        }
    
    def dump(self) -> str:
        """Export graph as GraphLang JSON"""
        return graph_to_json(self.graph)


# ═══ CLI ═══
if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='GraphLang On-Chain Tracer')
    p.add_argument('--wallet', '-w', required=True, help='Seed wallet address')
    p.add_argument('--depth', '-d', type=int, default=2, help='Trace depth (hops)')
    p.add_argument('--max', '-m', type=int, default=15, help='Max wallets per hop')
    p.add_argument('--output', '-o', help='Save graph to JSON file')
    
    args = p.parse_args()
    
    print("""
╔══════════════════════════════════════════════╗
║  GRAPHLANG ON-CHAIN TRACER                   ║
║  N=7 Structural Blockchain Forensics          ║
╚══════════════════════════════════════════════╝
""")
    
    tracer = GraphLangTracer(args.wallet)
    graph = tracer.trace(depth=args.depth, max_wallets=args.max)
    
    stats = tracer.stats()
    
    print(f"\n═══ GRAPHLANG TRACE RESULTS ═══")
    print(f"  Nodes:        {stats['nodes']}")
    print(f"  Edges:        {stats['edges']}")
    print(f"  Wallets:      {stats['wallets']}")
    print(f"  Transactions: {stats['transactions']}")
    print(f"  IR Kinds:     {stats['ir_kinds']}/7")
    print(f"  N value:      {stats['n_value']}")
    print(f"  SOL found:    {stats['total_sol_discovered']:,.2f}")
    print(f"  USD value:    ${stats['total_usd']:,.0f}")
    print(f"  Whales (>$5K): {stats['whales_found']}")
    
    if args.output:
        Path(args.output).write_text(tracer.dump())
        print(f"\n  Graph saved: {args.output}")
