/* NATKERNEL INTERRUPTS — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define IDT_SIZE 256
#define IRQ_BASE 32
#define IRQ_TIMER 0
#define IRQ_KBD 1
#define IRQ_MOUSE 12
#define IRQ_ATA_PRIMARY 14
#define IRQ_ATA_SECONDARY 15
#define IRQ_SYSCALL 0x80
#define PAGE_FAULT 14
#define GP_FAULT 13
#define DOUBLE_FAULT 8

/* struct */
typedef struct { u16 offset_low; u16 selector; u8 ist; u8 type_attr; u16 offset_mid; u32 offset_high; u32 reserved; } __attribute__((packed)) IDTEntry;
typedef struct { u64 r15,r14,r13,r12,r11,r10,r9,r8,rsi,rdi,rbp,rdx,rcx,rbx,rax; u64 int_no,err_code,rip,cs,rflags,rsp,ss; } IntFrame;

/* inline */
static inline void lidt(IDTEntry* base, u16 size) { struct { u16 limit; u64 base; } __attribute__((packed)) idtr = {size-1,(u64)base}; asm volatile("lidt %0"::"m"(idtr)); }
static inline void sti() { asm volatile("sti"); }
static inline void cli() { asm volatile("cli"); }

/* loop */
void init_idt() { for (u32 i = 0; i < IDT_SIZE; i++) { set_idt_gate(i, (u64)isr_stub, 0x08, 0x8E); } }

/* if */
void isr_handler(IntFrame* f) {
    if (f->int_no == IRQ_TIMER) { sched_tick(); }
    if (f->int_no == IRQ_KBD) { u8 sc = inb(0x60); kb_handler(sc); }
    if (f->int_no == IRQ_MOUSE) { u8 d = inb(0x60); }
    if (f->int_no == IRQ_SYSCALL) { f->rax = syscall_dispatch(f->rax, f->rdi, f->rsi, f->rdx); }
    if (f->int_no == PAGE_FAULT) { kernel_panic("Page Fault"); }
    if (f->int_no == GP_FAULT) { kernel_panic("GP Fault"); }
    if (f->int_no == DOUBLE_FAULT) { kernel_panic("Double Fault"); }
}

/* return */
void kernel_panic(const char* msg) { syscall_dispatch(SYS_WRITE, (u64)"PANIC: ", 7, NULL); syscall_dispatch(SYS_WRITE, (u64)msg, 0, NULL); while(1) asm volatile("hlt"); }
void set_idt_gate(u32 n, u64 handler, u16 sel, u8 flags) { idt[n].offset_low = handler & 0xFFFF; idt[n].selector = sel; idt[n].ist = 0; idt[n].type_attr = flags; idt[n].offset_mid = (handler>>16)&0xFFFF; idt[n].offset_high = (handler>>32)&0xFFFFFFFF; }
