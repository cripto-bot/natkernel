/* NATKERNEL IPC — from Linux ipc/ (18 files, 11K lines) */
#include "../kernel.h"

#define MAX_SEM 64
#define MAX_SHM 32
#define MAX_MSG 16
#define PIPE_SZ 4096

typedef struct { u32 id, val, waiters; } Semaphore;
typedef struct { u32 id; void* addr; u64 size; u32 owner; } ShmSeg;
typedef struct { u8 data[PIPE_SZ]; u32 head, tail; } Pipe;

static Semaphore sems[MAX_SEM];
static ShmSeg shms[MAX_SHM];
static Pipe pipes[32];

void ipc_init(void) {
    for(u32 i=0;i<MAX_SEM;i++){sems[i].id=i+1;sems[i].val=0;sems[i].waiters=0;}
    for(u32 i=0;i<PIPE_SZ;i++)pipes[i/128].data[i%128]=0;
}

/* Semaphores */
Semaphore* sem_create(u32 val) { for(u32 i=0;i<MAX_SEM;i++)if(sems[i].val==0&&sems[i].waiters==0){sems[i].val=val;return&sems[i];} return NULL; }
int sem_wait(Semaphore* s) { if(!s)return-1; while(s->val==0){s->waiters++;asm volatile("pause");s->waiters--;} s->val--; return 0; }
int sem_post(Semaphore* s) { if(!s)return-1; s->val++; return 0; }

/* Shared memory */
ShmSeg* shm_create(u64 size) { for(u32 i=0;i<MAX_SHM;i++)if(!shms[i].addr){shms[i].addr=alloc_page();shms[i].size=size;shms[i].id=i+1;return&shms[i];} return NULL; }
void* shm_attach(ShmSeg* s) { return s?s->addr:NULL; }
int shm_detach(ShmSeg* s) { if(s){s->addr=NULL;s->size=0;} return 0; }

/* Pipes */
int pipe_read(u32 id, void* buf, u32 len) {
    Pipe* p=&pipes[id%32]; u32 n=0;
    for(u32 i=0;i<len&&p->head!=p->tail;i++) { ((u8*)buf)[i]=p->data[p->tail]; p->tail=(p->tail+1)%PIPE_SZ; n++; }
    return n;
}
int pipe_write(u32 id, const void* buf, u32 len) {
    Pipe* p=&pipes[id%32]; u32 n=0;
    for(u32 i=0;i<len&&((p->tail+1)%PIPE_SZ)!=p->head;i++) { p->data[p->head]=((u8*)buf)[i]; p->head=(p->head+1)%PIPE_SZ; n++; }
    return n;
}
