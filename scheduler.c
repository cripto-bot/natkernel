/* NATKERNEL Scheduler — N=7 IR kinds */
#include "kernel.h"

static Process* current = NULL;
static Process procs[MAX_PROCESSES];
static u32 next_pid = 1;

/* IR-typedef: Process states */
#define PROC_READY   1
#define PROC_RUNNING 2
#define PROC_BLOCKED 3
#define PROC_ZOMBIE  4

/* IR-inline: Context switch */
static inline void ctx_switch(CPUContext* old, CPUContext* new) {
    asm volatile("pushq %%rax; pushq %%rbx; pushq %%rcx; pushq %%rdx;"
                 "pushq %%rsi; pushq %%rdi; pushq %%rbp;"
                 : : : "memory");
    kmemcpy(old, &((CPUContext){0}), sizeof(CPUContext));
    kmemcpy(&((CPUContext){0}), new, sizeof(CPUContext));
}

/* IR-loop: Round-robin */
static Process* round_robin() {
    if (current == NULL) return &procs[0];
    for (u32 i = 0; i < MAX_PROCESSES; i++) {
        u32 idx = (current->pid + 1 + i) % MAX_PROCESSES;
        if (procs[idx].state == PROC_READY) return &procs[idx];
    }
    return current;
}

/* IR-if: State transitions */
void sched_tick() {
    if (current) {
        current->state = PROC_READY;
    }
    Process* next = round_robin();
    if (next) {
        next->state = PROC_RUNNING;
        current = next;
    }
}

u32 sched_spawn(void (*entry)()) {
    if (next_pid >= MAX_PROCESSES) return 0;
    Process* p = &procs[next_pid++];
    p->pid = next_pid - 1;
    p->state = PROC_READY;
    p->ctx.rip = (u64)entry;
    p->ctx.rsp = (u64)&p->stack[STACK_SIZE - 8];
    return p->pid;
}

Process* sched_current() { return current; }
u32 sched_count() {
    u32 n = 0;
    for (u32 i = 0; i < MAX_PROCESSES; i++) {
        if (procs[i].state != 0) n++;
    }
    return n;
}
