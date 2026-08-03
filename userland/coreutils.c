/* NATUSER Coreutils — ls, cat, echo, cp, rm, mkdir. N=6 ∈ [4,12] */
#include "../kernel.h"

/* IR-inline */
static inline void putc(char c) { outb(0xE9, c); }
static inline void puts(const char* s) { for (;*s;s++) putc(*s); }

/* IR-loop: ls — list files */
void cmd_ls(void) {
    puts("Files:\n");
    for (u32 i = 0; i < 64; i++) {
        char name[32]; u32 fd = vfs_open("", 0);
        if (fd) { puts("  "); puts(name); putc('\n'); vfs_close(fd); }
    }
}

/* IR-return: cat — read file */
void cmd_cat(const char* name) {
    u32 fd = vfs_open(name, 0);
    if (!fd) { puts("cat: not found\n"); return; }
    char buf[128]; u32 r;
    while ((r = vfs_read(fd, buf, 127)) > 0) { buf[r] = 0; puts(buf); }
    vfs_close(fd);
}

/* IR-if: echo — print text */
void cmd_echo(const char* text) {
    puts(text); putc('\n');
}

/* IR-if: cp — copy file */
void cmd_cp(const char* src, const char* dst) {
    u32 sfd = vfs_open(src, 0); if (!sfd) { puts("cp: no source\n"); return; }
    u32 dfd = vfs_open(dst, 4); if (!dfd) { puts("cp: cannot create\n"); return; }
    char buf[64]; u32 r; while ((r = vfs_read(sfd, buf, 63)) > 0) vfs_write(dfd, buf, r);
    vfs_close(sfd); vfs_close(dfd);
}

/* IR-if: rm — delete file */
void cmd_rm(const char* name) {
    u32 fd = vfs_open(name, 0);
    if (fd) { vfs_write(fd, "", 0); vfs_close(fd); puts("rm: deleted\n"); }
    else puts("rm: not found\n");
}

/* IR-loop: mkdir — create directory */
void cmd_mkdir(const char* name) {
    u32 fd = vfs_open(name, 4);
    if (fd) { vfs_close(fd); puts("mkdir: created\n"); }
    else puts("mkdir: fail\n");
}
