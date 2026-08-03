/*
 * NATKERNEL — Universal Grammar Kernel
 * N=7 IR kinds: struct, define, inline, if, loop, typedef, extern
 * Designed by GraphLang. Architecture follows N∈[4,12].
 * Author: Josué Argaña Silguero
 */

/* IR-1: define — Constants */
#define NAT_VERSION     "0.1.0-grammar"
#define MAX_PROCESSES   256
#define STACK_SIZE      8192
#define PAGE_SIZE       4096
#define KERNEL_BASE     0xFFFF800000000000

/* IR-2: typedef — Type system */
typedef unsigned long   u64;
typedef unsigned int    u32;
typedef unsigned short  u16;
typedef unsigned char   u8;
typedef long            i64;
typedef int             i32;

/* IR-3: struct — Data structures */
typedef struct {
    u64 rax, rbx, rcx, rdx;
    u64 rsi, rdi, rbp, rsp;
    u64 r8, r9, r10, r11;
    u64 r12, r13, r14, r15;
    u64 rip, cs, rflags;
} __attribute__((packed)) CPUContext;

typedef struct {
    u32 pid;
    u32 state;
    CPUContext ctx;
    u8 stack[STACK_SIZE];
} Process;

typedef struct {
    Process* current;
    Process processes[MAX_PROCESSES];
    u32 count;
} Scheduler;

/* IR-4: extern — Global state */
static Scheduler sched;
static u64 tick_count = 0;

/* IR-5: inline — Core operations */
static inline void outb(u16 port, u8 val) {
    asm volatile("outb %0, %1" : : "a"(val), "Nd"(port));
}

static inline u8 inb(u16 port) {
    u8 val;
    asm volatile("inb %1, %0" : "=a"(val) : "Nd"(port));
    return val;
}

static inline void lidt(void* base, u16 size) {
    struct { u16 limit; u64 base; } __attribute__((packed)) idtr = {size, (u64)base};
    asm volatile("lidt %0" : : "m"(idtr));
}

/* IR-6: loop — Repetition patterns */
void kmemcpy(void* dst, const void* src, u64 n) {
    u8* d = (u8*)dst;
    const u8* s = (const u8*)src;
    for (u64 i = 0; i < n; i++) d[i] = s[i];
}

void kmemset(void* ptr, u8 value, u64 n) {
    u8* p = (u8*)ptr;
    for (u64 i = 0; i < n; i++) p[i] = value;
}

/* IR-7: if — Control flow */
u32 find_next_process() {
    u32 start = sched.current ? sched.current->pid : 0;
    for (u32 i = 1; i <= MAX_PROCESSES; i++) {
        u32 idx = (start + i) % MAX_PROCESSES;
        if (sched.processes[idx].state == 1) return idx;
    }
    return 0;
}

void schedule(CPUContext* ctx) {
    /* Save current context */
    if (sched.current) kmemcpy(&sched.current->ctx, ctx, sizeof(CPUContext));
    
    /* Find next */
    u32 next = find_next_process();
    if (next == 0) return;
    
    sched.current = &sched.processes[next];
    kmemcpy(ctx, &sched.current->ctx, sizeof(CPUContext));
}

/* Main kernel entry */
void kernel_main() {
    /* Clear */
    kmemset(&sched, 0, sizeof(Scheduler));
    
    /* Boot console */
    const char* msg = "\nNATKERNEL v" NAT_VERSION "\nArchitecture: N=7 [4,12]\nAuthor: Josue Argana Silguero\n";
    for (const char* c = msg; *c; c++) outb(0xE9, *c);
    
    /* Main kernel loop */
    for (;;) {
        tick_count++;
    }
}
