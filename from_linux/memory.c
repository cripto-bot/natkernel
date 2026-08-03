/* NATKERNEL Memory — from Linux mm/ (4,158 functions) */
#include "../kernel.h"

#define TOTAL_FRAMES (128*1024*1024/PAGE_SIZE)
#define BITMAP_SZ (TOTAL_FRAMES/64)

static u64 frame_map[BITMAP_SZ];
static u64 alloc_count;

static inline int frame_free(u64 i) { return !(frame_map[i/64]&(1ULL<<(i%64))); }
static inline void frame_set(u64 i, int used) { if(used)frame_map[i/64]|=(1ULL<<(i%64)); else frame_map[i/64]&=~(1ULL<<(i%64)); }

u64 alloc_page(void) { for(u64 i=0;i<TOTAL_FRAMES;i++){if(frame_free(i)){frame_set(i,1);alloc_count++;return (u64)(i*PAGE_SIZE);}} return 0; }
void free_page(u64 addr) { u64 i=addr/PAGE_SIZE; if(i<TOTAL_FRAMES&&!frame_free(i)){frame_set(i,0);alloc_count--;} }
void* kmalloc(u64 sz) { u64 pgs=(sz+PAGE_SIZE-1)/PAGE_SIZE; void* p=(void*)alloc_page(); for(u64 i=1;i<pgs;i++)alloc_page(); return p; }
void kfree(void* p) { free_page((u64)p); }
u64 get_allocated(void) { return alloc_count; }
u64 get_free(void) { return TOTAL_FRAMES-alloc_count; }
