#!/usr/bin/env python3
import socket, threading, time, random, struct

MIMIC_SITES = [
    ('wikipedia.org', 443), ('github.com', 443), ('stackoverflow.com', 443),
    ('reddit.com', 443), ('medium.com', 443), ('pypi.org', 443),
    ('arxiv.org', 443), ('dev.to', 443),
]

def mimic_burst():
    for _ in range(2):
        try:
            site, port = random.choice(MIMIC_SITES)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect((site, port))
            sock.send(b'\x16\x03\x01\x00\x60\x01\x00\x00\x5c\x03\x03' + 
                     bytes(random.randint(0,255) for _ in range(32)))
            sock.recv(512)
            sock.close()
        except: pass
        time.sleep(random.uniform(0.02, 0.06))

def handle_client(client_sock, addr):
    try:
        client_sock.recv(262)
        client_sock.send(b'\x05\x00')
        data = client_sock.recv(262)
        if len(data) < 10: return
        atyp, cmd = data[3], data[1]
        if atyp == 1:
            target_ip = socket.inet_ntoa(data[4:8])
            target_port = struct.unpack('!H', data[8:10])[0]
        elif atyp == 3:
            dl = data[4]
            target_ip = data[5:5+dl].decode()
            target_port = struct.unpack('!H', data[5+dl:7+dl])[0]
        else: return
        
        if cmd == 1:
            threading.Thread(target=mimic_burst, daemon=True).start()
            target = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            target.settimeout(30)
            target.connect((target_ip, target_port))
            client_sock.send(b'\x05\x00\x00\x01' + socket.inet_aton('0.0.0.0') + struct.pack('!H', 0))
            
            def relay(src, dst):
                while True:
                    try:
                        data = src.recv(8192)
                        if not data: break
                        dst.send(data)
                    except: break
            
            t1 = threading.Thread(target=relay, args=(client_sock, target), daemon=True)
            t2 = threading.Thread(target=relay, args=(target, client_sock), daemon=True)
            t1.start(); t2.start()
            t1.join(timeout=30); t2.join(timeout=30)
    except: pass
    finally:
        try: client_sock.close()
        except: pass

if __name__ == '__main__':
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 9050))
    server.listen(10)
    print("N7 PROXY: :9050")
    while True:
        client, addr = server.accept()
        threading.Thread(target=handle_client, args=(client, addr), daemon=True).start()
