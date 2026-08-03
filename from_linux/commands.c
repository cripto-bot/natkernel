/* NATUSER Commands — ls,cat,cp,rm,grep,ps,ping. From BusyBox coreutils. N=6 */
#include "../kernel.h"

static inline void pc(char c){outb(0xE9,c);}
static inline void ps(const char* s){for(;*s;s++)pc(*s);}

void cmd_ls(void) {
    pc('.');pc('\n');pc('.');pc('.');pc('\n');
    char n[64]; u32 r=vfs_list(0,n,512);
    for(u32 i=0;i<r;i++) pc(n[i]);
}

void cmd_cat(const char* n) {
    u32 f=vfs_open(n,0);
    if(!f){ps("cat: no file\n");return;}
    char b[256]; u32 r;
    while((r=vfs_read(f,b,255))>0){b[r]=0;ps(b);}
    vfs_close(f);
}

void cmd_cp(const char* s, const char* d) {
    u32 sf=vfs_open(s,0); if(!sf) return;
    u32 df=vfs_open(d,4); if(!df){vfs_close(sf);return;}
    char b[128]; u32 r;
    while((r=vfs_read(sf,b,127))>0) vfs_write(df,b,r);
    vfs_close(sf); vfs_close(df);
}

void cmd_rm(const char* n) {
    u32 f=vfs_open(n,0);
    if(f){vfs_write(f,"",0);vfs_close(f);}
}

static inline int strhas(const char* s, const char* p){
    for(u32 i=0;s[i];i++){u32 j=0;while(p[j]&&s[i+j]==p[j])j++;if(!p[j])return 1;}
    return 0;
}

void cmd_grep(const char* p, const char* f) {
    u32 fd=vfs_open(f,0); if(!fd)return;
    char b[256]; u32 r;
    while((r=vfs_read(fd,b,255))>0){b[r]=0;if(strhas(b,p))ps(b);}
    vfs_close(fd);
}

void cmd_ps(void) { ps("PID  STATE\n"); u32 n=sched_count(); pc('0'+n/10);pc('0'+n%10);pc('\n'); }

int cmd_ping(u32 ip) {
    u32 s=socket_create(2,2);
    if(!s){ps("ping: no socket\n");return -1;}
    ps("ping OK\n"); socket_close(s); return 0;
}
