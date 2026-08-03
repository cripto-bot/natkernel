/* NATKERNEL Virtual Memory — N=7 IR kinds */
#include "kernel.h"

#define PAGE_PRESENT  1
#define PAGE_WRITABLE 2
#define PAGE_USER     4
#define TOTAL_PAGES   (256 * 1024 * 1024 / PAGE_SIZE)
#define BITMAP_SIZE   (TOTAL_PAGES / 8)

typedef struct {
    u64 entries[512];
} __attribute__((aligned(PAGE_SIZE))) PageTable;

static u8 alloc_bitmap[BITMAP_SIZE];
static PageTable kernel_pml4 __attribute__((aligned(PAGE_SIZE)));
static u64 total_allocated = 0;

static inline int bit_test(u8* bitmap, u64 idx) {
    return (bitmap[idx / 8] >> (idx % 8)) & 1;
}
static inline void bit_set(u8* bitmap, u64 idx) {
    bitmap[idx / 8] |= (1 << (idx % 8));
}
static inline void bit_clear(u8* bitmap, u64 idx) {
    bitmap[idx / 8] &= ~(1 << (idx % 8));
}

u64 alloc_page() {
    for (u64 i = 0; i < TOTAL_PAGES; i++) {
        if (bit_test(alloc_bitmap, i) == 0) {
            bit_set(alloc_bitmap, i);
            total_allocated++;
            return i * PAGE_SIZE;
        }
    }
    return 0;
}

void free_page(u64 addr) {
    u64 idx = addr / PAGE_SIZE;
    if (idx < TOTAL_PAGES) {
        if (bit_test(alloc_bitmap, idx)) {
            bit_clear(alloc_bitmap, idx);
            total_allocated--;
        }
    }
}

void map_page(u64 vaddr, u64 paddr, u64 flags) {
    u64 l4 = (vaddr >> 39) & 0x1FFULL;
    u64 l3 = (vaddr >> 30) & 0x1FFULL;
    u64 l2 = (vaddr >> 21) & 0x1FFULL;
    u64 l1 = (vaddr >> 12) & 0x1FFULL;
    
    if (kernel_pml4.entries[l4] == 0) {
        u64 new_pt = alloc_page();
        kernel_pml4.entries[l4] = new_pt | PAGE_PRESENT | PAGE_WRITABLE;
    }
    
    PageTable* l3_table = (PageTable*)(kernel_pml4.entries[l4] & ~0xFFF);
    if (l3_table->entries[l3] == 0) {
        u64 new_pt = alloc_page();
        l3_table->entries[l3] = new_pt | PAGE_PRESENT | PAGE_WRITABLE;
    }
    
    PageTable* l2_table = (PageTable*)(l3_table->entries[l3] & ~0xFFF);
    if (l2_table->entries[l2] == 0) {
        u64 new_pt = alloc_page();
        l2_table->entries[l2] = new_pt | PAGE_PRESENT | PAGE_WRITABLE;
    }
    
    PageTable* l1_table = (PageTable*)(l2_table->entries[l2] & ~0xFFF);
    l1_table->entries[l1] = paddr | flags;
}

u64 get_allocated() { return total_allocated; }
