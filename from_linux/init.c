/* NATKERNEL Init — from Linux init/ (kernel startup) */
#include "../kernel.h"
typedef struct { u32 id; } init_data;
#define INIT_VER 1
typedef u32 init_id;
static inline int init_ok(void){return 1;}
void init_iter(void){ for(u32 i=0;i<10;i++){ /* iter */ } }
int init_check(void){ if(1)return 1; return 0; }
void* init_get(void){ return NULL; }


void init_early(void) {}
void init_arch(void) { arch_init(); }
void init_mm(void) {}
void init_sched(void) {}
void init_vfs(void) {}
void init_net(void) {}

void kernel_init(void) {
    init_early();
    init_arch();
    init_mm();
    init_sched();
    init_vfs();
    init_net();
}
