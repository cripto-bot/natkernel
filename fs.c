/* NATKERNEL Filesystem — N=7 IR kinds */
#include "kernel.h"

/* IR-define: FS constants */
#define MAX_FILES   64
#define MAX_NAME    32
#define MAX_FSIZE   4096

/* IR-struct: File descriptor */
typedef struct {
    char name[MAX_NAME];
    u8* data;
    u32 size;
    u32 in_use;
} File;

/* IR-typedef: Global state */
static File file_table[MAX_FILES];

/* IR-loop: Find free slot */
static File* find_free() {
    for (u32 i = 0; i < MAX_FILES; i++) {
        if (file_table[i].in_use == 0) return &file_table[i];
    }
    return NULL;
}

/* IR-loop: Find by name */
static File* find_file(const char* name) {
    for (u32 i = 0; i < MAX_FILES; i++) {
        if (file_table[i].in_use == 0) continue;
        int match = 1;
        for (u32 j = 0; j < MAX_NAME; j++) {
            if (file_table[i].name[j] != name[j]) { match = 0; break; }
            if (name[j] == 0) break;
        }
        if (match) return &file_table[i];
    }
    return NULL;
}

/* IR-inline: Operations */
static inline u32 name_copy(char* dst, const char* src) {
    u32 i;
    for (i = 0; i < MAX_NAME - 1 && src[i]; i++) dst[i] = src[i];
    dst[i] = 0;
    return i;
}

/* IR-if: Create file */
u32 fs_create(const char* name, u32 size) {
    File* f = find_free();
    if (f == NULL) return 0;
    if (size > MAX_FSIZE) size = MAX_FSIZE;
    
    f->data = (u8*)alloc_page();
    if (f->data == NULL) return 0;
    
    name_copy(f->name, name);
    f->size = size;
    f->in_use = 1;
    return (u32)((u64)f - (u64)file_table) / sizeof(File);
}

/* IR-return: Read/Write */
u32 fs_read(u32 fd, void* buf, u64 len) {
    if (fd >= MAX_FILES) return 0;
    File* f = &file_table[fd];
    if (f->in_use == 0) return 0;
    if (len > f->size) len = f->size;
    kmemcpy(buf, f->data, len);
    return len;
}

u32 fs_write(u32 fd, const void* buf, u64 len) {
    if (fd >= MAX_FILES) return 0;
    File* f = &file_table[fd];
    if (f->in_use == 0) return 0;
    if (len > f->size) len = f->size;
    kmemcpy(f->data, buf, len);
    return len;
}
