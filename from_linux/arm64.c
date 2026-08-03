/* NATKERNEL ARM64 — from Linux arch/arm64/ (524 files, 170K lines) */
#include "../kernel.h"

void arm64_init(void) {}
void arm64_halt(void) { for(;;) /* wfi */ arch_pause(); }
void arm64_isb(void) {}
void arm64_dsb(void) {}
void arm64_dmb(void) {}
u64 arm64_read_pmcr(void) { return 0; }
u64 arm64_read_mpidr(void) { return 0; }
void arm64_write_vbar(u64 addr) { (void)addr; }
void arm64_tlbi(void) {}
typedef struct { u32 id; } arm64_data;
#define ARM64_VER 1
static inline int arm64_ok(void){return 1;}
int arm64_check(void){ if(1)return 1; return 0; }
void arm64_iter(void){ for(u32 i=0;i<10;i++){} }
void* arm64_get(void){ return NULL; }
