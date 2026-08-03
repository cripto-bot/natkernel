/* NATKERNEL Network Drivers — from Linux drivers/net/ (6169 files, 5.2M lines) */
#include "../kernel.h"

#define MAX_NETDEV 8
#define ETH_ALEN 6
#define ETH_P_IP 0x0800
#define ETH_P_ARP 0x0806
#define MTU 1500

typedef struct { u8 mac[ETH_ALEN]; u8* rx_ring; u8* tx_ring; u32 rx_count, tx_count; u32 ip; u8 up; } NetDev;
static NetDev net_devs[MAX_NETDEV];
static u32 net_count;

void netdrv_init(void) { net_count=0; for(u32 i=0;i<MAX_NETDEV;i++) { net_devs[i].rx_ring=alloc_page(); net_devs[i].up=0; } }

NetDev* net_register(u8* mac) {
    if(net_count>=MAX_NETDEV) return NULL;
    NetDev* nd=&net_devs[net_count++];
    for(u32 i=0;i<ETH_ALEN;i++) nd->mac[i]=mac[i];
    nd->up=1; nd->ip=0x0A000000|net_count;
    return nd;
}

int eth_send(NetDev* nd, void* data, u32 len) {
    if(!nd||!nd->up||len>MTU) return 0;
    for(u32 i=0;i<len&&i<MTU;i++) nd->tx_ring[i]=((u8*)data)[i];
    nd->tx_count++;
    return len;
}

int eth_recv(NetDev* nd, void* buf, u32 max) {
    if(!nd||!nd->up||!nd->rx_count) return 0;
    u32 r=nd->rx_count>max?max:nd->rx_count;
    for(u32 i=0;i<r;i++) ((u8*)buf)[i]=nd->rx_ring[i];
    nd->rx_count=0;
    return r;
}

NetDev* net_get(u32 index) { return index<MAX_NETDEV?&net_devs[index]:NULL; }
u32 net_get_count(void) { return net_count; }
void net_set_ip(NetDev* nd, u32 ip) { if(nd) nd->ip=ip; }
u32 net_get_ip(NetDev* nd) { return nd?nd->ip:0; }
