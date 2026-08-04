/* TCPIP — N=6 */
#include "../kernel.h"

// Forward declarations
u32 socket_alloc(u32 ip, u16 port);
void tcp_send(TCPSocket* sk, void* data, u32 len);
void ip_send(IPHeader* ip, u32 len);''',

#define ETH_ALEN      6
#define IP_MAX_PACKET  65535
#define TCP_MAX_SEG    1460
#define MAX_SEG        1460
#define MAX_SOCKETS    1024
#define BACKLOG        128
#define SOCK_STREAM    1
#define AF_INET        2
#define IPPROTO_TCP    6
#define TCP_SYN        0x02
#define TCP_ACK        0x10
#define TCP_FIN        0x01
#define TCP_RST        0x04
typedef struct { u32 ip; u16 port; u32 peer_ip; u16 peer_port; u32 state; u32 seq; u32 ack; u32 rx_len; u8* rx_buf; } TCPSocket;
typedef struct { u32 src; u32 dst; u8 proto; u8 ttl; u16 id; u16 len; u16 checksum; } IPHeader;
TCPSocket* socket_table[MAX_SOCKETS];
static inline u16 ip_checksum(void* data, u32 len) { u32 sum = 0; u16* p = (u16*)data; for (u32 i = 0; i < len/2; i++) { sum += p[i]; if (sum > 0xFFFF) sum = (sum & 0xFFFF) + 1; } return (u16)~sum; }
static inline u32 tcp_checksum(TCPSocket* sk, void* data, u32 len) { u32 sum = sk->ip + sk->peer_ip + IPPROTO_TCP + len; return ip_checksum(data, len); }
static inline int socket_hash(u32 ip, u16 port) { return (ip ^ port) % MAX_SOCKETS; }
void tcp_send(TCPSocket* sk, void* data, u32 len) {
    u8 buf[1500];
    IPHeader* ip = (IPHeader*)buf;
    ip->src = sk->ip; ip->dst = sk->peer_ip; ip->proto = IPPROTO_TCP;
    ip->ttl = 64; ip->len = len + 40;
    for (u32 i = 0; i < len; i += TCP_MAX_SEG) {
        u32 seg = (len - i > TCP_MAX_SEG) ? TCP_MAX_SEG : (len - i);
        ip->checksum = ip_checksum(ip, 20);
        sk->seq += seg;
    }
}
void ip_send(IPHeader* ip, u32 len) {}
TCPSocket* tcp_accept(TCPSocket* sk) {
    if (sk == NULL || sk->state != 2) return NULL;
    u32 new_fd = socket_alloc(sk->ip, sk->peer_port);
    if (new_fd == 0) return NULL;
    TCPSocket* ns = socket_table[new_fd];
    ns->ip = sk->ip; ns->port = sk->peer_port;
    ns->peer_ip = sk->ip; ns->peer_port = sk->port;
    ns->state = 3; ns->seq = sk->ack;
    return ns;
}
TCPSocket* socket_lookup(u32 ip, u16 port) {
    u32 idx = socket_hash(ip, port);
    return socket_table[idx];
}
u32 socket_alloc(u32 ip, u16 port) {
    for (u32 i = 0; i < MAX_SOCKETS; i++) {
        if (socket_table[i] == NULL) {
            socket_table[i] = (TCPSocket*)alloc_page();
            socket_table[i]->ip = ip; socket_table[i]->port = port;
            socket_table[i]->state = 1;
            return i;
        }
    }
    return 0;
}
