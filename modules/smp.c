/* SMP Subsystem — N=5 IR kinds */
#include <natkernel/smp.h>

#define MAX_CPUS        64
#define TLB_SHOOTDOWN   0x01
#define IPI_RESCHEDULE  0x02
#define IPI_CALL_FUNC   0x03
#define IPI_CPU_STOP    0x04
#define PERCPU_OFFSET   0x1000

static inline void send_ipi(u32 cpu, u32 vector) { *(volatile u32*)(0xFEE00000 + cpu*0x1000) = vector; }
static inline u32 get_cpu_id() { u32 id; asm volatile("movl %%gs:0, %0" : "=r"(id)); return id; }
static inline void xchg(u32* a, u32* b) { u32 t = *a; *a = *b; *b = t; }
int cpu_online(u32 cpu) {
    if (cpu >= MAX_CPUS) return 0;
    if (percpu[cpu].online == 0) return 0;
    return 1;
}
void smp_init() {
    for (u32 cpu = 0; cpu < MAX_CPUS; cpu++) {
        if (cpu == 0) { percpu[cpu].online = 1; continue; }
        percpu[cpu].cpu_id = cpu;
        percpu[cpu].stack = alloc_page();
        percpu[cpu].gdt = alloc_page();
        if (percpu[cpu].stack && percpu[cpu].gdt) {
            send_ipi(cpu, 0x40);
            percpu[cpu].online = 1;
        }
    }
}
