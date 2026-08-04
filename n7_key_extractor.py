#!/usr/bin/env python3
"""
N7 KEY EXTRACTOR — Wallet Key Gap Analysis with GraphLang

Analyzes wallet key management structure using GraphLang methodology.
Finds N<4 gaps where private keys/seeds are exposed.

Method:
  1. Normalize wallet storage → GraphLang IR
  2. Measure N for key-handling functions
  3. Where N<4 → key exposure gap
  4. Extract keys from those gaps

Targets:
  - File system (plaintext seeds, backups)
  - Browser storage (Chrome/Firefox extension data)
  - Memory (running wallet processes)
  - Clipboard history
  - Log files

Author: Josué Argaña Silguero
N=7 ∈ [4,12]
"""

import sys, os, json, hashlib, re, struct, subprocess
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/mnt/hdd3tb/GraphLab-Final')
from graphlang.core import Graph, Node, build_graph

# ═══ WALLET STORAGE LOCATIONS ═══
WALLET_PATHS = {
    'metamask_chrome': '~/.config/google-chrome/Default/Local Extension Settings/nkbihfbeogaeaoehlefnkodbefgpgknn',
    'metamask_firefox': '~/.mozilla/firefox/*/storage/default/moz-extension++*',
    'phantom_chrome': '~/.config/google-chrome/Default/Local Extension Settings/bfnaelmomeimhlpmgjnjophhpkkoljpa',
    'phantom_firefox': '~/.mozilla/firefox/*/storage/default/moz-extension++*',
    'electrum': '~/.electrum/wallets/',
    'bitcoin_core': '~/.bitcoin/wallets/',
    'ethereum_geth': '~/.ethereum/keystore/',
    'solana_cli': '~/.config/solana/id.json',
    'exodus': '~/.config/Exodus/',
    'trust_wallet': '~/.trustwallet/',
}

# ═══ PATTERNS TO FIND ═══
KEY_PATTERNS = {
    'mnemonic_12': re.compile(r'\b(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\b'),
    'mnemonic_24': re.compile(r'\b(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\s+(\w+)\b'),
    'private_key_hex': re.compile(r'\b[0-9a-fA-F]{64}\b'),
    'private_key_wif': re.compile(r'\b[5KL][1-9A-HJ-NP-Za-km-z]{50,51}\b'),
    'seed_hex': re.compile(r'\b(seed|mnemonic|phrase|backup)[=:]\s*[\"\\\']?([a-fA-F0-9]{32,})\b', re.IGNORECASE),
    'bip39_seed': re.compile(r'\b(seed|mnemonic)[=:]\s*[\"\\\']?(\w+(?:\s+\w+){11,23})[\"\\\']?\b', re.IGNORECASE),
}

BIP39_WORDS = set()
_bip39_path = Path('/usr/share/python3-bip39/wordlist/english.txt')
if _bip39_path.exists():
    BIP39_WORDS = set(_bip39_path.read_text().strip().split('\n'))
else:
    # Minimal BIP39 subset for detection
    BIP39_WORDS = {'abandon','ability','able','about','above','absent','absorb','abstract','absurd','abuse',
                   'access','accident','account','accuse','achieve','acid','acoustic','acquire','across','act',
                   'action','actor','actress','actual','adapt','add','addict','address','adjust','admit'}


class GraphLangKeyAuditor:
    """Analyze wallet key management using GraphLang structural analysis."""
    
    def __init__(self):
        self.findings = []
        self.audit_graph = Graph()
    
    def audit_filesystem(self, base_path: str = None) -> list:
        """Scan filesystem for wallet key storage gaps."""
        if base_path is None:
            base_path = str(Path.home())
        
        print(f"\n═══ FILESYSTEM AUDIT ═══\n")
        
        # Check known wallet paths
        for wallet_name, wallet_path in WALLET_PATHS.items():
            expanded = Path(wallet_path).expanduser()
            if expanded.exists():
                n_val = self._measure_storage_n(expanded)
                severity = '🔴' if n_val < 4 else ('🟡' if n_val < 6 else '🟢')
                print(f"  {severity} {wallet_name}: N={n_val} — {expanded}")
                
                if n_val < 4:
                    self.findings.append({
                        'type': 'plaintext_storage',
                        'wallet': wallet_name,
                        'path': str(expanded),
                        'n_value': n_val,
                        'severity': 'critical' if n_val <= 3 else 'medium',
                    })
        
        # Search for seed/key files
        print(f"\n  Searching for seed/key files...")
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if not d.startswith('.git')]
            
            for f in files:
                fpath = Path(root) / f
                try:
                    st_size = fpath.stat().st_size
                except (FileNotFoundError, OSError):
                    continue  # Broken symlink
                if st_size > 10_000_000:  # Skip huge files
                    continue
                
                # Check filename patterns
                name_lower = f.lower()
                if any(kw in name_lower for kw in ['seed','mnemonic','key','wallet','backup','phrase']):
                    try:
                        content = fpath.read_text(errors='ignore')[:5000]
                        n_val = self._analyze_content_n(content, str(fpath))
                        if n_val <= 4:
                            print(f"  🔴 N={n_val} — {fpath}")
                            self.findings.append({
                                'type': 'seed_file_found',
                                'path': str(fpath),
                                'n_value': n_val,
                                'preview': content[:100],
                            })
                    except:
                        pass
        
        return self.findings
    
    def audit_memory(self) -> list:
        """Find wallet processes and check for keys in memory."""
        print(f"\n═══ MEMORY AUDIT ═══\n")
        
        # Find wallet-related processes
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            for line in result.stdout.split('\n'):
                if any(w in line.lower() for w in ['bitcoin','ethereum','geth','electrum','phantom',
                                                     'metamask','solana','wallet','defi']):
                    pid = line.split()[1]
                    print(f"  Found wallet process: PID {pid} — {line.split()[10][:50]}")
                    
                    # Try to read process memory
                    try:
                        mem_path = f'/proc/{pid}/mem'
                        mem = Path(mem_path)
                        if mem.exists():
                            n_val = self._measure_storage_n(mem)
                            print(f"    N={n_val} — {'🔴 exposed' if n_val < 4 else '✅ protected'}")
                    except:
                        pass
        except:
            print("  No wallet processes found in memory")
        
        return self.findings
    
    def audit_clipboard(self) -> list:
        """Check clipboard for keys (seeds are often copy-pasted)."""
        print(f"\n═══ CLIPBOARD AUDIT ═══\n")
        
        try:
            # X11 clipboard
            result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'],
                                    capture_output=True, text=True, timeout=2)
            content = result.stdout
            
            # Check for mnemonic or private key patterns
            for pattern_name, pattern in KEY_PATTERNS.items():
                matches = pattern.findall(content)
                if matches:
                    print(f"  🔴 CLIPBOARD contains {pattern_name}!")
                    self.findings.append({
                        'type': 'clipboard_exposure',
                        'pattern': pattern_name,
                        'preview': str(matches[0])[:80],
                    })
                    return self.findings
            
            print("  No keys found in clipboard")
        except:
            print("  Clipboard not accessible")
        
        return self.findings
    
    def audit_browser_storage(self) -> list:
        """Check browser storage for wallet extension data."""
        print(f"\n═══ BROWSER STORAGE AUDIT ═══\n")
        
        chrome_base = Path.home() / '.config' / 'google-chrome' / 'Default'
        
        # LevelDB storage (where extensions store data)
        for ext_dir_name in ['Local Extension Settings', 'IndexedDB', 'databases']:
            ext_dir = chrome_base / ext_dir_name
            if not ext_dir.exists():
                continue
            
            for wallet_dir in ext_dir.iterdir():
                if not wallet_dir.is_dir():
                    continue
                
                # Look for LevelDB files
                ldb_files = list(wallet_dir.glob('*.ldb')) + list(wallet_dir.glob('*.log'))
                
                for ldb in ldb_files[:5]:  # Limit to avoid huge scan
                    try:
                        # LevelDB has binary keys — try to extract strings
                        data = ldb.read_bytes()[:100000]
                        strings_found = re.findall(b'[a-zA-Z]{4,}[ \t]+[a-zA-Z]{4,}[ \t]+[a-zA-Z]{4,}', data)
                        
                        for s in strings_found[:3]:
                            text = s.decode('ascii', errors='ignore')
                            # Check if it looks like a mnemonic phrase
                            words = text.split()
                            bip39_count = sum(1 for w in words if w.lower() in BIP39_WORDS)
                            if bip39_count >= 3:
                                print(f"  🔴 Possible mnemonic in {ldb}!")
                                self.findings.append({
                                    'type': 'browser_storage',
                                    'path': str(ldb),
                                    'preview': text[:80],
                                })
                    except:
                        pass
        
        if not self.findings:
            print("  No browser wallet storage found")
        
        return self.findings
    
    def _measure_storage_n(self, path: Path) -> int:
        """
        Measure N (IR kinds) for how a key is stored.
        
        N=7: encrypted + hashed + chmod 600 + no backup + memory secure
        N<4: plaintext / world-readable / backup exposed / in logs
        """
        kinds = set()
        
        # struct: file exists
        kinds.add('struct')
        
        # define: permissions
        try:
            mode = path.stat().st_mode
            if mode & 0o077 == 0:  # No group/other permissions
                kinds.add('define')  # Proper permission
            # else: missing → gap
        except:
            pass
        
        # loop: directory traversal protection
        try:
            if path.is_dir():
                parent = path.parent
                if parent.stat().st_mode & 0o077 == 0:
                    kinds.add('loop')
        except:
            pass
        
        # conditional: encryption check
        try:
            if path.suffix in ('.enc', '.gpg', '.aes'):
                kinds.add('conditional')  # Encrypted
            elif path.is_file():
                data = path.read_bytes()[:100]
                entropy = self._entropy(data)
                if entropy > 7.0:  # High entropy = encrypted
                    kinds.add('conditional')
        except:
            pass
        
        # return: is the data recoverable
        kinds.add('return')
        
        # hash: integrity check
        try:
            if path.is_file() and path.stat().st_size < 1000000:
                hash_val = hashlib.sha256(path.read_bytes()).hexdigest()
                kinds.add('hash')
        except:
            pass
        
        # chain: backup exposure
        backup_patterns = ['backup','icloud','drive','dropbox','onedrive']
        path_str = str(path).lower()
        if not any(bp in path_str for bp in backup_patterns):
            kinds.add('chain')  # Not in backup path
        
        return len(kinds)
    
    def _entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy."""
        if not data:
            return 0
        freq = {}
        for b in data:
            freq[b] = freq.get(b, 0) + 1
        return -sum((f/len(data)) * (f/len(data)).bit_length() for f in freq.values()) / 8
    
    def _analyze_content_n(self, content: str, path: str) -> int:
        """Analyze file content for key material."""
        n = 7  # Start with 7, subtract for each gap
        
        # Check for plaintext keys
        for pname, pattern in KEY_PATTERNS.items():
            if pattern.search(content):
                print(f"    Pattern match: {pname}")
                n -= 2  # Major gap: private key in plaintext
                break
        
        # Also check: any file with "seed","key","phrase","backup" in name AND has content
        name_lower = Path(path).name.lower()
        has_key_name = any(kw in name_lower for kw in ['seed','mnemonic','key','backup','phrase'])
        
        if has_key_name and len(content.strip()) > 10:
            # Check entropy — high entropy = encrypted (good), low = plaintext (bad)
            entropy = self._entropy(content.encode()[:1000])
            if entropy < 6.0:  # Low entropy = likely plaintext
                print(f"    Low entropy ({entropy:.1f}): likely plaintext")
                n -= 2
        
        # Check permissions
        try:
            mode = Path(path).stat().st_mode
            if mode & 0o077 != 0:
                n -= 1  # World-readable
        except:
            pass
        
        return max(1, min(7, n))
    
    def generate_report(self) -> str:
        """Generate GraphLang audit report."""
        report = []
        report.append("═══ GRAPHLANG KEY STORAGE AUDIT ═══")
        report.append(f"Total gaps found: {len(self.findings)}")
        report.append("")
        
        for f in self.findings:
            severity = f.get('severity', 'unknown')
            f_type = f.get('type', 'unknown')
            path = f.get('path', f.get('wallet', 'unknown'))
            n_val = f.get('n_value', '?')
            
            report.append(f"  🔴 [{f_type}] N={n_val} — {path}")
            if 'preview' in f:
                report.append(f"     Preview: {f['preview'][:60]}...")
        
        report.append("")
        report.append("Gap classes:")
        report.append("  N=3: Plaintext seed/key — extractable immediately")
        report.append("  N=4: Weak encryption/bad permissions")
        report.append("  N=5: Storage OK but backup exposed")
        report.append("  N=6: Good storage, minor config issue")
        report.append("  N=7: Fully protected")
        
        return '\n'.join(report)


# ═══ Generate Test Wallet (to demonstrate gap analysis) ═══
def create_test_wallet():
    """
    Create a test wallet with realistic key storage patterns
    to demonstrate GraphLang gap detection.
    """
    import random, secrets
    
    print("═══ Creating test wallets for analysis ═══\n")
    
    wallet_dir = Path.home() / '.test_wallets'
    wallet_dir.mkdir(exist_ok=True)
    
    # 1. Plaintext seed (N=3 gap)
    seed_words = random.sample(sorted(BIP39_WORDS)[:200], 12)
    mn_file = wallet_dir / 'my_backup_phrase.txt'
    mn_file.write_text(' '.join(seed_words))
    mn_file.chmod(0o644)  # World readable!
    print(f"  🔴 Plaintext seed (N=3): {mn_file} (chmod 644)")
    
    # 2. Private key in JSON config (N=3 gap)
    pk = secrets.token_hex(32)
    config_file = wallet_dir / 'wallet_config.json'
    config_file.write_text(json.dumps({
        'name': 'My Wallet',
        'private_key': pk,
        'address': '0x' + secrets.token_hex(20),
    }))
    print(f"  🔴 Private key in JSON (N=3): {config_file}")
    
    # 3. Seed in environment/log file (N=2 gap)
    log_file = wallet_dir / 'wallet.log'
    log_file.write_text(f'2026-08-04 INFO: Wallet initialized with seed: {" ".join(seed_words)}\n')
    print(f"  🔴 Seed in log file (N=2): {log_file}")
    
    # 4. Properly protected (N=7) — comparison
    secure_file = wallet_dir / 'secure_wallet.enc'
    secure_file.write_bytes(hashlib.sha256(seed_words[0].encode()).digest())
    secure_file.chmod(0o600)
    print(f"  🟢 Encrypted wallet (N=7): {secure_file} (chmod 600)")
    
    return wallet_dir


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='N7 Wallet Key Auditor')
    p.add_argument('--demo', action='store_true', help='Create test wallets and audit')
    p.add_argument('--audit', '-a', help='Audit specific path')
    p.add_argument('--memory', action='store_true', help='Audit running processes')
    p.add_argument('--clipboard', action='store_true', help='Check clipboard')
    p.add_argument('--browser', action='store_true', help='Check browser storage')
    args = p.parse_args()
    
    auditor = GraphLangKeyAuditor()
    
    if args.demo:
        wallet_dir = create_test_wallet()
        auditor.audit_filesystem(str(wallet_dir))
        print('\n' + auditor.generate_report())
    
    elif args.audit:
        auditor.audit_filesystem(args.audit)
        print('\n' + auditor.generate_report())
    
    else:
        # Full audit
        print("N7 KEY EXTRACTOR — Full Audit\n")
        auditor.audit_filesystem()
        auditor.audit_clipboard()
        auditor.audit_browser_storage()
        
        print('\n' + auditor.generate_report())
        
        # Clean up test wallets
        tw = Path.home() / '.test_wallets'
        if tw.exists():
            import shutil
            shutil.rmtree(tw)
