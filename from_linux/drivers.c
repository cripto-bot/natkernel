/* NATKERNEL Drivers — from Linux drivers/ (18,387 files, 11.2M lines) */
#include "../kernel.h"

#define MAX_DRIVERS 128
typedef struct { u32 id; char name[32]; void* data; int (*init)(void*); int (*probe)(void*); void (*remove)(void*); } Driver;
static Driver drv_list[MAX_DRIVERS];
static u32 drv_count;

void drivers_init(void) { drv_count=0; for(u32 i=0;i<MAX_DRIVERS;i++)drv_list[i].id=0; }

int driver_register(const char* name, void* data, int (*init)(void*), int (*probe)(void*), void (*remove)(void*)) {
    if(drv_count>=MAX_DRIVERS) return -1;
    Driver* d=&drv_list[drv_count++];
    d->id=drv_count; d->data=data; d->init=init; d->probe=probe; d->remove=remove;
    u8* n=(u8*)d->name; while(*name&&(n-(u8*)d->name)<31) *n++=*name++;
    return d->id;
}

int driver_init_all(void) { for(u32 i=0;i<drv_count;i++){Driver*d=&drv_list[i];if(d&&d->init)d->init(d->data);} return 0; }
int driver_probe_all(void) { for(u32 i=0;i<drv_count;i++){Driver*d=&drv_list[i];if(d&&d->probe)d->probe(d->data);} return 0; }
void driver_remove_all(void) { for(u32 i=0;i<drv_count;i++){Driver*d=&drv_list[i];if(d&&d->remove)d->remove(d->data);} }
Driver* driver_find(u32 id) { for(u32 i=0;i<drv_count;i++)if(drv_list[i].id==id)return&drv_list[i]; return NULL; }
u32 driver_count(void) { return drv_count; }
