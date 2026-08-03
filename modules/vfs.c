/* NATKERNEL VFS — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define VFS_MAX_MOUNTS 16
#define VFS_MAX_FD 256
#define O_RDONLY 0
#define O_WRONLY 1
#define O_RDWR 2
#define O_CREAT 0100
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2

/* struct */
typedef struct { u32 ino; u32 offset; u32 flags; void* fs_data; } VFSFile;
typedef struct { char name[32]; u32 ino; u32 parent; u32 size; u16 mode; u32 uid; u32 gid; } VFSInode;
VFSFile fd_table[VFS_MAX_FD];
VFSInode inode_table[MAX_FILES];

/* inline */
static inline VFSFile* fd_get(u32 fd) { return (fd < VFS_MAX_FD) ? &fd_table[fd] : NULL; }

/* loop */
u32 vfs_open(const char* name, u32 flags) { u32 ino = 0; for (u32 i = 0; i < MAX_FILES; i++) { int match = 1; for (u32 j = 0; j < 32 && name[j]; j++) { if (inode_table[i].name[j] != name[j]) { match = 0; break; } } if (match && inode_table[i].size > 0) { ino = i; break; } } if (ino == 0) return 0; u32 fd = 0; for (u32 i = 0; i < VFS_MAX_FD; i++) { if (fd_table[i].ino == 0) { fd = i; break; } } fd_table[fd].ino = ino; fd_table[fd].offset = 0; fd_table[fd].flags = flags; return fd; }

/* if */
u32 vfs_read(u32 fd, void* buf, u32 len) { VFSFile* f = fd_get(fd); if (!f || f->ino == 0) return 0; if (f->ino < MAX_FILES) { u32 max_len = inode_table[f->ino].size - f->offset; if (len > max_len) len = max_len; u32 r = fs_read(f->ino, buf, len); f->offset += r; return r; } return 0; }

/* return */
u32 vfs_write(u32 fd, const void* buf, u32 len) { VFSFile* f = fd_get(fd); if (!f || f->ino == 0) return 0; fs_write(f->ino, buf, len); return len; }
void vfs_close(u32 fd) { if (fd < VFS_MAX_FD) { fd_table[fd].ino = 0; fd_table[fd].offset = 0; } }
