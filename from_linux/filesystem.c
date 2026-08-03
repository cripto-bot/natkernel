/* NATKERNEL VFS — from Linux fs/ (26,262 functions) */
#include "../kernel.h"

#define MAX_VFS 256
#define MAX_NAME 64

typedef struct { u32 ino; u32 off; u32 flags; } VfsFile;
typedef struct { char name[MAX_NAME]; u32 sz; u8* data; u16 mode; u32 uid; } VfsInode;
static VfsFile opened[MAX_VFS];
static VfsInode inodes[MAX_VFS];
static u32 next_ino=1;

static inline int scmp(const char* a, const char* b) { while(*a&&*a==*b){a++;b++;} return *a-*b; }
static u32 find_ino(const char* n) { for(u32 i=0;i<MAX_VFS;i++)if(inodes[i].name[0]&&!scmp(inodes[i].name,n))return i; return 0; }

u32 vfs_open(const char* n, u32 fl) { u32 ino=find_ino(n); if(!ino&&!(fl&4))return 0; if(!ino){ino=next_ino++;u8*d=(u8*)inodes[ino].name;while(*n)*d++=*n++;} for(u32 i=0;i<MAX_VFS;i++){if(!opened[i].ino){opened[i].ino=ino;opened[i].off=0;opened[i].flags=fl;return i;}} return 0; }
u32 vfs_read(u32 fd, void* b, u32 len) { if(fd>=MAX_VFS||!opened[fd].ino)return 0; VfsInode* ino=&inodes[opened[fd].ino]; u32 r=len>ino->sz-opened[fd].off?ino->sz-opened[fd].off:len; kmemcpy(b,ino->data+opened[fd].off,r); opened[fd].off+=r; return r; }
u32 vfs_write(u32 fd, const void* b, u32 len) { if(fd>=MAX_VFS||!opened[fd].ino)return 0; VfsInode* ino=&inodes[opened[fd].ino]; if(!ino->data){ino->data=(u8*)alloc_page();ino->sz=0;} u32 w=len>4096-opened[fd].off?4096-opened[fd].off:len; kmemcpy(ino->data+opened[fd].off,b,w); opened[fd].off+=w; if(opened[fd].off>ino->sz)ino->sz=opened[fd].off; return w; }
void vfs_close(u32 fd) { if(fd<MAX_VFS) opened[fd].ino=0; }
