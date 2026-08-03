/* NATKERNEL Syscalls — N=7 IR kinds */
#include "kernel.h"

/* IR-define: Syscall numbers */
#define SYS_WRITE  0
#define SYS_READ   1
#define SYS_EXIT   2
#define SYS_SBRK   3
#define SYS_GETPID 4
#define SYS_FORK   5
#define SYS_EXEC   6

/* IR-struct: Syscall table */
static void* syscall_table[7];

/* IR-inline: Syscall helpers */
static inline u64 sys_read(void* buf, u64 len) {
    u64 i;
    for (i = 0; i < len; i++) {
        ((u8*)buf)[i] = inb(0x60);
    }
    return i;
}

static inline u64 sys_write(const void* buf, u64 len) {
    for (u64 i = 0; i < len; i++) {
        outb(0xE9, ((const u8*)buf)[i]);
    }
    return len;
}

static inline u64 sys_exit(u32 code) {
    Process* p = sched_current();
    if (p) p->state = PROC_ZOMBIE;
    return code;
}

static inline u64 sys_getpid() {
    Process* p = sched_current();
    return p ? p->pid : 0;
}

static inline u64 sys_sbrk(i64 increment) {
    return alloc_page();
}

static inline u64 sys_fork() {
    Process* parent = sched_current();
    if (!parent) return 0;
    
    u32 child_pid = sched_spawn(NULL);
    if (child_pid == 0) return 0;
    
    Process* child = NULL;
    for (u32 i = 0; i < MAX_PROCESSES; i++) {
        Process* p = &sched_procs(i);
        if (p && p->pid == child_pid) { child = p; break; }
    }
    if (!child) return 0;
    
    kmemcpy(child, parent, sizeof(Process));
    child->pid = child_pid;
    child->ctx.rsp = (u64)&child->stack[STACK_SIZE - 8];
    return 0;
}

/* IR-if: Syscall dispatcher */
u64 syscall_dispatch(u64 num, u64 arg1, u64 arg2, u64 arg3) {
    if (num == SYS_WRITE) return sys_write((void*)arg1, arg2);
    if (num == SYS_READ)  return sys_read((void*)arg1, arg2);
    if (num == SYS_EXIT)  return sys_exit((u32)arg1);
    if (num == SYS_SBRK)  return sys_sbrk((i64)arg1);
    if (num == SYS_GETPID) return sys_getpid();
    if (num == SYS_FORK)  return sys_fork();
    return 0;
}

/* IR-return: Init */
void sys_init() {
    kmemset(syscall_table, 0, sizeof(syscall_table));
}
