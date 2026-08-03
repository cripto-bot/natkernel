/* NATKERNEL — Universal Grammar Kernel
 * N=7 IR kinds: struct, define, typedef, inline, loop, if, return
 * Author: Josué Argaña Silguero
 * License: MII Open License v1.0
 */

#ifndef NATKERNEL_H
#define NATKERNEL_H

#define NULL ((void*)0)

/* IR-define: Architecture constants */
#define NAT_VERSION     "0.2.0"
#define MAX_PROCESSES   256
#define STACK_SIZE      8192
#define PAGE_SIZE       4096
#define KERNEL_BASE     0xFFFF800000000000

/* IR-typedef: Core types */
typedef unsigned long      u64;
typedef unsigned int       u32;
typedef unsigned short     u16;
typedef unsigned char      u8;
typedef long               i64;
typedef int                i32;

/* IR-struct: CPU context for context switching */
typedef struct {
    u64 rax, rbx, rcx, rdx, rsi, rdi, rbp, rsp;
    u64 r8, r9, r10, r11, r12, r13, r14, r15;
    u64 rip, cs, rflags;
} __attribute__((packed)) CPUContext;

/* IR-struct: Process control block */
typedef struct {
    u32 pid;
    u32 state;
    CPUContext ctx;
    u8 stack[STACK_SIZE];
} Process;

#define PROC_READY   1
#define PROC_RUNNING 2
#define PROC_BLOCKED 3
#define PROC_ZOMBIE  4

/* Syscall numbers */
#define SYS_WRITE  0
#define SYS_READ   1
#define SYS_EXIT   2
#define SYS_SBRK   3
#define SYS_GETPID 4
#define SYS_FORK   5

/* IR-inline: IO operations */
static inline void outb(u16 port, u8 val) {
    asm volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}
static inline u8 inb(u16 port) {
    u8 val;
    asm volatile("inb %1, %0" : "=a"(val) : "Nd"(port));
    return val;
}

static inline void kmemcpy(void* d, const void* s, u64 n) {
    for (u64 i = 0; i < n; i++) ((u8*)d)[i] = ((const u8*)s)[i];
}
static inline void kmemset(void* p, u8 v, u64 n) {
    for (u64 i = 0; i < n; i++) ((u8*)p)[i] = v;
}

/* IR-extern: Module declarations */
/* scheduler */
u32 sched_spawn(void (*entry)());
void sched_tick();
Process* sched_current();
u32 sched_count();
Process* sched_procs(u32 i);

/* memory */
u64 alloc_page();
void free_page(u64 addr);
void map_page(u64 vaddr, u64 paddr, u64 flags);
u64 get_allocated();

/* syscall */
void sys_init();
u64 syscall_dispatch(u64 num, u64 a1, u64 a2, u64 a3);

/* fs */
u32 fs_create(const char* name, u32 size);
u32 fs_read(u32 fd, void* buf, u64 len);
u32 fs_write(u32 fd, const void* buf, u64 len);

/* fs from_linux */
u32 vfs_open(const char* n, u32 fl);
u32 vfs_read(u32 fd, void* b, u32 len);
u32 vfs_write(u32 fd, const void* b, u32 len);
void vfs_close(u32 fd);
/* network from_linux */
u32 socket_create(u32 fam, u32 type);

/* from_linux modules */
void usb_init(void);
void pci_init(void);
void net_init(void);
void arch_init(void);
void audio_init(void);
void gpu_init(void);
void virt_init(void);
void ipc_init(void);
void crypto_init(void);
void block_init(void);
void nvme_init(void);
void input_init(void);

/* main */
void kernel_main();

#endif
