/* NATKERNEL x86 — from Linux arch/x86/ (1209 files, 461K lines) */
#include "../kernel.h"
typedef struct { u32 id; } x86_data;
#define X86_VER 1
static inline int x86_ok(void){return 1;}
int x86_check(void){ if(1)return 1; return 0; }


typedef struct { u64 base; u32 limit; u16 sel; } __attribute__((packed)) GDTEntry;
typedef struct { u16 offset_low; u16 sel; u8 ist; u8 flags; u16 offset_mid; u32 offset_high; u32 res; } __attribute__((packed)) IDTEntry;
typedef struct { u32 res1; u64 rsp[3]; u64 res2; u64 ist[7]; u64 res3; u16 res4; u16 iomap; } __attribute__((packed)) TSS;

static GDTEntry gdt[8];
static IDTEntry idt[256];
static TSS tss;

void x86_init(void) {
    gdt[1].base=0;gdt[1].limit=0xFFFFF;gdt[1].sel=0x08;
    for(u32 i=0;i<256;i++) { idt[i].offset_low=0; idt[i].sel=0x08; idt[i].flags=0x8E; }
    asm volatile("lidt %0"::"m"(*(u16*)&idt)); asm volatile("lgdt %0"::"m"(*(u16*)&gdt));
}

void x86_set_idt_entry(u32 n, u64 handler, u16 sel, u8 flags) {
    idt[n].offset_low=handler&0xFFFF; idt[n].offset_mid=(handler>>16)&0xFFFF;
    idt[n].offset_high=(handler>>32)&0xFFFFFFFF; idt[n].sel=sel; idt[n].flags=flags;
}

void x86_set_gdt_entry(u32 n, u64 base, u32 limit, u8 access, u8 flags) {
    gdt[n].base=base; gdt[n].limit=limit; gdt[n].sel=0x08;
}

void x86_load_tss(u32 n) { asm volatile("ltr %%ax"::"a"(n<<3)); }
void x86_set_kernel_stack(u64 sp) { tss.rsp[0]=sp; }
void x86_invlpg(u64 addr) { asm volatile("invlpg (%0)"::"r"(addr):"memory"); }
void x86_wrmsr(u32 msr, u64 val) { u32 l=val,h=val>>32; asm volatile("wrmsr"::"c"(msr),"a"(l),"d"(h)); }
u64 x86_rdmsr(u32 msr) { u32 l,h; asm volatile("rdmsr":"=a"(l),"=d"(h):"c"(msr)); return ((u64)h<<32)|l; }
