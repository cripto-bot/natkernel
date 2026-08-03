/* NATKERNEL Block — from Linux drivers/block/ (90 files, 96K lines) */
#include "../kernel.h"

#define MAX_BLK 32
#define BLK_SZ 512

typedef struct { u32 id; u64 sectors; u8* data; u32 r_ops, w_ops; } BlkDev;
static BlkDev blk_devs[MAX_BLK];

void block_init(void) {
    for(u32 i=0;i<MAX_BLK;i++) {
        blk_devs[i].id=i+1;
        blk_devs[i].sectors=1024;
        blk_devs[i].data=(u8*)alloc_page();
        blk_devs[i].r_ops=0; blk_devs[i].w_ops=0;
    }
}

BlkDev* block_find(u32 id) {
    for(u32 i=0;i<MAX_BLK;i++) if(blk_devs[i].id==id) return &blk_devs[i];
    return NULL;
}

int block_read(u32 id, u64 sector, void* buf, u32 count) {
    BlkDev* d=block_find(id);
    if(!d||sector+count>d->sectors) return 0;
    for(u32 i=0;i<count;i++) {
        u64 off=(sector+i)*BLK_SZ;
        for(u32 j=0;j<BLK_SZ;j++) ((u8*)buf)[i*BLK_SZ+j]=d->data[off+j];
    }
    d->r_ops+=count;
    return count;
}

int block_write(u32 id, u64 sector, const void* buf, u32 count) {
    BlkDev* d=block_find(id);
    if(!d||sector+count>d->sectors) return 0;
    for(u32 i=0;i<count;i++) {
        u64 off=(sector+i)*BLK_SZ;
        for(u32 j=0;j<BLK_SZ;j++) d->data[off+j]=((u8*)buf)[i*BLK_SZ+j];
    }
    d->w_ops+=count;
    return count;
}

u64 block_size(u32 id) { BlkDev* d=block_find(id); return d?d->sectors:0; }
u32 block_reads(u32 id) { BlkDev* d=block_find(id); return d?d->r_ops:0; }
u32 block_writes(u32 id) { BlkDev* d=block_find(id); return d?d->w_ops:0; }
