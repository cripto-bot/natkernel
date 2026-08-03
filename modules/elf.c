/* NATKERNEL ELF — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define ELF_MAGIC 0x464C457F
#define ELF_PT_LOAD 1
#define PF_X 1
#define PF_W 2
#define PF_R 4

/* struct */
typedef struct { u32 magic; u8 elf[12]; u16 type; u16 machine; u32 version; u64 entry; u64 phoff; u64 shoff; u32 flags; u16 ehsize; u16 phentsize; u16 phnum; u16 shentsize; u16 shnum; u16 shstrndx; } Elf64Header;
typedef struct { u32 type; u32 flags; u64 offset; u64 vaddr; u64 paddr; u64 filesz; u64 memsz; u64 align; } Elf64ProgHeader;

/* inline */
static inline int elf_check(Elf64Header* h) { return h->magic == ELF_MAGIC && (h->machine == 0x3E || h->machine == 0xB7); }

/* loop */
int elf_load(void* data, u64* entry) { Elf64Header* eh = (Elf64Header*)data; if (!elf_check(eh)) return 0; for (u16 i = 0; i < eh->phnum; i++) { Elf64ProgHeader* ph = (Elf64ProgHeader*)((u8*)data + eh->phoff + i*eh->phentsize); if (ph->type == ELF_PT_LOAD) { for (u64 j = 0; j < ph->memsz; j += PAGE_SIZE) { u64 page = alloc_page(); map_page(ph->vaddr+j, page, PAGE_PRESENT|PAGE_WRITABLE|PAGE_USER); } } } *entry = eh->entry; return 1; }

/* if */
int exec_elf(const char* path) { u32 fd = fs_open(path); if (fd == 0) return -1; void* buf = (void*)alloc_page(); fs_read(fd, buf, PAGE_SIZE); u64 entry; if (elf_load(buf, &entry)) { Process* p = sched_current(); p->ctx.rip = entry; return 0; } return -2; }
