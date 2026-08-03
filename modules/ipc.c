/* NATKERNEL IPC — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define SIGKILL 9
#define SIGTERM 15
#define SIGINT 2
#define PIPE_SIZE 4096
#define MAX_PIPES 64

/* struct */
typedef struct { u8 buf[PIPE_SIZE]; u32 head,tail; u32 readers,writers; } Pipe;

/* inline */
static inline int pipe_full(Pipe* p) { return ((p->tail+1) % PIPE_SIZE) == p->head; }
static inline int pipe_empty(Pipe* p) { return p->head == p->tail; }

/* loop */
u32 pipe_read(Pipe* p, void* buf, u32 len) { u32 n = 0; for (u32 i = 0; i < len && !pipe_empty(p); i++) { ((u8*)buf)[i] = p->buf[p->tail]; p->tail = (p->tail+1) % PIPE_SIZE; n++; } return n; }

/* if */
u32 pipe_write(Pipe* p, const void* buf, u32 len) { u32 n = 0; for (u32 i = 0; i < len && !pipe_full(p); i++) { p->buf[p->head] = ((u8*)buf)[i]; p->head = (p->head+1) % PIPE_SIZE; n++; } return n; }

/* return */
Pipe* pipe_create() { for (u32 i = 0; i < MAX_PIPES; i++) { if (pipes[i].readers == 0) { pipes[i].head = 0; pipes[i].tail = 0; pipes[i].readers = 1; return &pipes[i]; } } return NULL; }
