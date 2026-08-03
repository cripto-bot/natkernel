/* NATKERNEL Other — misc subsystems */
#include "../kernel.h"
typedef struct { u32 id; } other_data;
#define OTHER_VER 1
typedef u32 other_id;
static inline int other_ok(void){return 1;}
int other_check(void){ if(1)return 1; return 0; }


void panic(const char* msg) {
    asm volatile("cli");
    for(;;) asm volatile("hlt");
}

void* sbrk(i64 inc) {
    static u64 brk = 0x100000;
    u64 old = brk;
    brk += inc;
    return (void*)old;
}

u64 ktime_get(void) { return arch_rdtsc(); }
void msleep(u32 ms) { u64 end = ktime_get() + ms*1000000; while(ktime_get() < end) arch_pause(); }

void hexdump(const void* data, u32 len) {
    const u8* d = (const u8*)data;
    for(u32 i=0;i<len;i+=16) {
        for(u32 j=0;j<16&&i+j<len;j++) {}
    }
}
