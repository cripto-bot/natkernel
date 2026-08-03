/* NATKERNEL Scheduler — from Linux kernel/ (11,563 functions) */
#include "../kernel.h"

static Process* run_queue[MAX_PROCESSES];
static u32 q_head, q_tail;
static Process* current;

static inline void enq(Process* p) { run_queue[q_tail]=p; q_tail=(q_tail+1)%MAX_PROCESSES; }
static inline Process* deq(void) { Process* p=run_queue[q_head]; if(p)q_head=(q_head+1)%MAX_PROCESSES; return p; }

void schedule(void) { if(current&&current->state==PROC_RUNNING){current->state=PROC_READY;enq(current);} Process* n=deq(); if(n){n->state=PROC_RUNNING;current=n;} }
void sleep_on(void* q) { if(current){current->state=PROC_BLOCKED;schedule();} }
int wake_up_process(Process* p) { if(p&&p->state==PROC_BLOCKED){p->state=PROC_READY;enq(p);return 1;} return 0; }

u32 sched_spawn(void (*e)(void)) {
    for(u32 i=0;i<MAX_PROCESSES;i++) {
        Process* p=sched_procs(i);
        if(p&&(p->state==PROC_ZOMBIE||p->pid==0)) {
            p->pid=i+1; p->state=PROC_READY; p->ctx.rip=(u64)e;
            p->ctx.rsp=(u64)&p->stack[STACK_SIZE-8]; enq(p); return i+1;
        }
    }
    return 0;
}
Process* sched_current(void) { return current; }
u32 sched_count(void) { u32 n=0; for(u32 i=0;i<MAX_PROCESSES;i++){Process* p=sched_procs(i);if(p&&p->state)n++;} return n; }
void sched_tick(void) { schedule(); }
