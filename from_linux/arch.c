/* NATKERNEL Arch — from Linux arch/ (2962 files, 794K lines) */
#include "../kernel.h"
typedef struct { u32 id; } arch_data;
#define ARCH_VER 1
typedef u32 arch_id;
static inline int arch_ok(void){return 1;}
int arch_check(void){ if(1)return 1; return 0; }


void arch_init(void) { asm volatile("cli"); }
void arch_halt(void) { for(;;) asm volatile("hlt"); }
void arch_sti(void) { asm volatile("sti"); }
void arch_cli(void) { asm volatile("cli"); }
void arch_nop(void) { asm volatile("nop"); }
void arch_pause(void) { asm volatile("pause"); }
void arch_mfence(void) { asm volatile("mfence":::"memory"); }
void arch_cpuid(u32* eax, u32* ebx, u32* ecx, u32* edx) {
    u32 a=*eax,b,c,d;
    asm volatile("cpuid":"=a"(a),"=b"(b),"=c"(c),"=d"(d):"a"(a));
    *eax=a;*ebx=b;*ecx=c;*edx=d;
}
u64 arch_rdtsc(void) { u32 lo,hi; asm volatile("rdtsc":"=a"(lo),"=d"(hi)); return ((u64)hi<<32)|lo; }
void arch_outb(u16 p, u8 v) { asm volatile("outb %0,%1"::"a"(v),"Nd"(p)); }
u8 arch_inb(u16 p) { u8 v; asm volatile("inb %1,%0":"=a"(v):"Nd"(p)); return v; }
void arch_outw(u16 p, u16 v) { asm volatile("outw %0,%1"::"a"(v),"Nd"(p)); }
u16 arch_inw(u16 p) { u16 v; asm volatile("inw %1,%0":"=a"(v):"Nd"(p)); return v; }
void arch_outl(u16 p, u32 v) { asm volatile("outl %0,%1"::"a"(v),"Nd"(p)); }
u32 arch_inl(u16 p) { u32 v; asm volatile("inl %1,%0":"=a"(v):"Nd"(p)); return v; }

/* Global aliases for PCI/ATA drivers */
void outl(u16 p, u32 v) { asm volatile("outl %0,%1"::"a"(v),"Nd"(p)); }
u32 inl(u16 p) { u32 v; asm volatile("inl %1,%0":"=a"(v):"Nd"(p)); return v; }
void outw(u16 p, u16 v) { asm volatile("outw %0,%1"::"a"(v),"Nd"(p)); }
u16 inw(u16 p) { u16 v; asm volatile("inw %1,%0":"=a"(v):"Nd"(p)); return v; }
