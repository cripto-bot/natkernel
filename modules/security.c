/* NATKERNEL SECURITY — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define MAX_USERS 64
#define MAX_GROUPS 32
#define ROOT_UID 0
#define S_IRWXU 0700
#define S_IRUSR 0400
#define S_IWUSR 0200
#define S_IXUSR 0100
#define S_IRWXG 0070
#define S_IRWXO 0007

/* struct */
typedef struct { u32 uid; u32 gid; char name[32]; char home[64]; } User;
typedef struct { u32 owner; u32 group; u16 mode; } Permissions;
User user_table[MAX_USERS];

/* inline */
static inline int check_perm(Permissions* p, u32 uid, u32 gid, u8 bits) {
    if (uid == ROOT_UID) return 1;
    if (uid == p->owner) return (p->mode & bits) != 0;
    if (gid == p->group) return (p->mode & (bits>>3)) != 0;
    return (p->mode & (bits>>6)) != 0;
}

/* if */
int fs_check_access(u32 ino, u8 access) {
    u32 uid = sched_current() ? sched_current()->uid : 0;
    u32 gid = sched_current() ? sched_current()->gid : 0;
    if (ino >= MAX_FILES) return 0;
    Permissions* p = &file_perms[ino];
    return check_perm(p, uid, gid, access);
}

/* return */
User* user_find(u32 uid) { if (uid >= MAX_USERS) return NULL; return user_table[uid].name[0] ? &user_table[uid] : NULL; }
