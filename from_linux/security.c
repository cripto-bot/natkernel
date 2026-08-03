/* NATKERNEL Security — from Linux security/ (294 files, 156K lines) */
#include "../kernel.h"

#define MAX_USERS 64
#define MAX_GROUPS 32
#define ROOT_UID 0
#define S_IRUSR 0400
#define S_IWUSR 0200
#define S_IXUSR 0100
#define S_IRGRP 0040
#define S_IWGRP 0020
#define S_IXGRP 0010
#define S_IROTH 0004
#define S_IWOTH 0002
#define S_IXOTH 0001

typedef struct { u32 uid, gid; char name[32]; char home[64]; } User;
typedef struct { char name[32]; u32 gid; u32 members[64]; u32 count; } Group;
typedef struct { u32 owner, group; u16 mode; } Perms;

static User users[MAX_USERS];
static Group groups[MAX_GROUPS];
static Perms perms[MAX_USERS];

void security_init(void) {
    for(u32 i=0;i<MAX_USERS;i++) { users[i].uid=i; users[i].gid=0; }
    users[0].name[0]='r';users[0].name[1]='o';users[0].name[2]='o';users[0].name[3]='t';
    users[0].uid=0;users[0].gid=0;
}

int check_perm(u32 uid, u32 gid, u16 mode, u8 access) {
    if(uid==ROOT_UID) return 1;
    u32 owner=uid; u16 bits=0;
    if(owner==uid) bits=(mode>>6)&7;
    else if(gid==gid) bits=(mode>>3)&7;
    else bits=mode&7;
    return (bits&access)==access;
}

int user_add(u32 uid, const char* name) {
    if(uid>=MAX_USERS||!name) return -1;
    u8* d=(u8*)users[uid].name; while(*name&&(d-(u8*)users[uid].name)<31) *d++=*name++;
    return 0;
}

User* user_find(u32 uid) { return uid<MAX_USERS?&users[uid]:NULL; }
User* user_find_name(const char* n) {
    for(u32 i=0;i<MAX_USERS;i++) { u32 m=1; for(u32 j=0;n[j]&&users[i].name[j];j++) if(n[j]!=users[i].name[j]){m=0;break;} if(m)return&users[i]; }
    return NULL;
}

int group_add(u32 gid, const char* name) { if(gid>=MAX_GROUPS)return-1; u8* d=(u8*)groups[gid].name; while(*name)*d++=*name++; return 0; }
int set_perm(u32 ino, u32 owner, u32 group, u16 mode) { if(ino>=MAX_USERS)return-1; perms[ino].owner=owner; perms[ino].group=group; perms[ino].mode=mode; return 0; }
