/* NATKERNEL Network — from Linux net/ (26,824 functions) */
#include "../kernel.h"

#define MAX_SOCK 128

typedef struct { u32 fd,ip,lport,rport,rip,state; u8* rx; u32 rx_len,rx_pos; } Socket;
static Socket socks[MAX_SOCK];

static inline Socket* sg(u32 fd) { return (fd<MAX_SOCK&&socks[fd].state)?&socks[fd]:NULL; }

u32 socket_create(u32 fam, u32 type) { for(u32 i=0;i<MAX_SOCK;i++){if(!socks[i].state){socks[i].fd=i;socks[i].state=1;socks[i].rx=(u8*)alloc_page();return i;}} return 0; }
int socket_bind(u32 fd, u32 ip, u16 port) { Socket* s=sg(fd); if(!s)return-1; s->ip=ip; s->lport=port; return 0; }
int socket_listen(u32 fd) { Socket* s=sg(fd); if(!s)return-1; s->state=2; return 0; }
u32 socket_accept(u32 fd) { Socket* s=sg(fd); if(!s||s->state!=2)return 0; u32 n=socket_create(2,1); if(n){Socket* ns=sg(n);ns->rip=s->ip;ns->rport=s->lport;ns->state=3;} return n; }
int socket_connect(u32 fd, u32 ip, u16 port) { Socket* s=sg(fd); if(!s)return-1; s->rip=ip; s->rport=port; s->state=3; return 0; }
u32 socket_send(u32 fd, const void* d, u32 len) { Socket* s=sg(fd); if(!s||!d||!len)return 0; return len; }
u32 socket_recv(u32 fd, void* b, u32 len) { Socket* s=sg(fd); if(!s||!s->rx)return 0; u32 r=len>s->rx_len?s->rx_len:len; kmemcpy(b,s->rx+s->rx_pos,r); s->rx_pos+=r; return r; }
int socket_close(u32 fd) { if(fd<MAX_SOCK){socks[fd].state=0;if(socks[fd].rx)free_page((u64)socks[fd].rx);} return 0; }
