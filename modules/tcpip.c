/* TCP/IP Stack — N=6 IR kinds */
#include <natkernel/net.h>

#define ETH_ALEN      6
#define IP_MAX_PACKET  65535
#define TCP_MAX_SEG    1460
#define UDP_MAX_DGRAM  65507
#define SOCK_STREAM    1
#define SOCK_DGRAM     2
#define AF_INET        2
#define IPPROTO_TCP    6
#define IPPROTO_UDP    17
#define TCP_SYN        0x02
#define TCP_ACK        0x10
#define TCP_FIN        0x01
#define TCP_RST        0x04
#define MAX_SOCKETS    1024
#define BACKLOG        128
typedef struct { u32 src_ip; u32 dst_ip; u16 src_port; u16 dst_port; u32 seq; u32 ack; u8 flags; u16 window; u8* data; u32 len; } TCPPacket;
typedef struct { u32 ip; u16 port; u32 state; u32 seq; u32 ack; void* rx_buf; u32 rx_len; } TCPSocket;
typedef struct { u32 src; u32 dst; u8 proto; u8 ttl; u16 id; u16 len; } __attribute__((packed)) IPHeader;
TCPSocket* socket_table[MAX_SOCKETS];

static inline u16 ip_checksum(void* data, u32 len) { u32 sum = 0; u16* p = (u16*)data; for (u32 i = 0; i < len/2; i++) { sum += p[i]; if (sum > 0xFFFF) sum = (sum & 0xFFFF) + 1; } return ~(u16)sum; }
static inline u32 tcp_checksum(TCPPacket* pkt) { u32 sum = 0; sum += pkt->src_ip; sum += pkt->dst_ip; sum += IPPROTO_TCP; sum += pkt->len; return ip_checksum(pkt->data, pkt->len + 12); }
static inline int socket_hash(u32 ip, u16 port) { return (ip ^ port) % MAX_SOCKETS; }
u32 tcp_send(u32 sock_fd, void* data, u32 len) {
    TCPSocket* sk = socket_table[sock_fd];
    if (sk == NULL) return 0;
    TCPPacket pkt;
    pkt.src_ip = sk->ip; pkt.src_port = sk->port;
    pkt.dst_ip = sk->peer_ip; pkt.dst_port = sk->peer_port;
    pkt.seq = sk->seq; pkt.ack = sk->ack;
    pkt.flags = TCP_ACK; pkt.data = data; pkt.len = len;
    for (u32 i = 0; i < len; i += MAX_SEG) {
        u32 seg = (len - i > MAX_SEG) ? MAX_SEG : (len - i);
        pkt.len = seg;
        pkt.checksum = tcp_checksum(&pkt);
        ip_send(&pkt);
        sk->seq += seg;
    }
    return len;
}
void ip_send(TCPPacket* pkt) {
    IPHeader ip = {pkt->src_ip, pkt->dst_ip, IPPROTO_TCP, 64, 0, pkt->len + sizeof(IPHeader)};
    ip.checksum = ip_checksum(&ip, sizeof(IPHeader));
    eth_transmit(&ip, sizeof(IPHeader));
}
u32 tcp_accept(u32 listen_fd) {
    TCPSocket* sk = socket_table[listen_fd];
    if (sk == NULL || sk->state != 2) return 0;
    u32 new_fd = socket_alloc();
    if (new_fd == 0) return 0;
    TCPSocket* new_sk = socket_table[new_fd];
    new_sk->ip = sk->ip; new_sk->port = sk->peer_port; new_sk->state = 3;
    TCPPacket synack = {sk->ip, sk->peer_ip, sk->port, sk->peer_port, sk->seq, 0, TCP_SYN|TCP_ACK, 8192, 0, 0};
    tcp_send(listen_fd, &synack, 0);
    return new_fd;
}
TCPSocket* socket_lookup(u32 ip, u16 port) {
    u32 idx = socket_hash(ip, port);
    return socket_table[idx];
}
u32 socket_alloc() {
    for (u32 i = 0; i < MAX_SOCKETS; i++) {
        if (socket_table[i] == NULL) {
            socket_table[i] = (TCPSocket*)alloc_page();
            return i;
        }
    }
    return 0;
}
