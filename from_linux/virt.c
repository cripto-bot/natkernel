/* NATKERNEL Virt — from Linux virt/ (59 files, 21K lines) */
#include "../kernel.h"

#define MAX_VM 8
#define VM_STATE_STOPPED 0
#define VM_STATE_RUNNING 1
#define VM_MEM_MB 64

typedef struct { u32 id, state; void* mem; u64 mem_sz; void* vcpu; } VM;
static VM vms[MAX_VM];

void virt_init(void) { for(u32 i=0;i<MAX_VM;i++){vms[i].id=i+1;vms[i].state=0;vms[i].mem=NULL;} }

VM* vm_create(u64 mem_mb) {
    for(u32 i=0;i<MAX_VM;i++) {
        if(vms[i].state==VM_STATE_STOPPED) {
            vms[i].mem=alloc_page();
            vms[i].mem_sz=mem_mb*1024*1024;
            vms[i].state=VM_STATE_STOPPED;
            return &vms[i];
        }
    }
    return NULL;
}

int vm_start(VM* vm) { if(vm&&vm->mem){vm->state=VM_STATE_RUNNING;return 0;} return -1; }
int vm_stop(VM* vm) { if(vm){vm->state=VM_STATE_STOPPED;return 0;} return -1; }
int vm_pause(VM* vm) { if(vm&&vm->state==VM_STATE_RUNNING){vm->state=VM_STATE_STOPPED;return 0;} return -1; }
void* vm_memory(VM* vm) { return vm?vm->mem:NULL; }

void vm_inject_irq(VM* vm, u32 vector) {}
void vm_set_reg(VM* vm, u32 reg, u64 val) {}
u64 vm_get_reg(VM* vm, u32 reg) { return 0; }
u32 vm_count(void) { u32 n=0; for(u32 i=0;i<MAX_VM;i++)if(vms[i].state)n++; return n; }
