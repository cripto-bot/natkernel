/* NATKERNEL POWER — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define POWER_OFF_PORT 0x604
#define REBOOT_PORT 0x64
#define REBOOT_CMD 0xFE

/* inline */
static inline void outw(u16 port, u16 val) { asm volatile("outw %0, %1"::"a"(val),"Nd"(port)); }

/* if */
void cpu_idle() { if (sched_count() > 0) { asm volatile("hlt"); } }

/* return */
void power_off() { outw(POWER_OFF_PORT, 0x2000); while(1) asm volatile("hlt"); }
void reboot() { u8 g; while((inb(0x64)&2)!=0); outb(REBOOT_PORT, REBOOT_CMD); while(1) asm volatile("hlt"); }
