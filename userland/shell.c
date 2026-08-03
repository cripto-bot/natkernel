/* NATUSER Shell — from BusyBox shell/ (14 files, 29,939 lines, N=7) */
#include "../kernel.h"

#define MAX_LINE 256
#define MAX_ARGS 32
static char line[MAX_LINE];
static char* argv[MAX_ARGS];

static inline int seq(const char* a, const char* b) { while(*a&&*a==*b){a++;b++;} return *a==*b; }

void shell_run(void) {
    for(;;) {
        for(const char* p="$ ";*p;p++) outb(0xE9,*p);
        u32 pos=0;
        for(u32 i=0;i<MAX_LINE-1;i++) {
            u8 c=inb(0x60);
            if(c==0x1C){line[i]=0;break;}
            if(c>='a'&&c<='z') line[i]=c;
        }
        if(!line[0]) continue;
        u32 argc=0; char* p=line;
        while(*p==' ') p++;
        if(!*p) continue;
        argv[argc++]=p;
        while(*p) {
            if(*p==' ') { *p=0; p++; while(*p==' ') p++;
                if(*p&&argc<MAX_ARGS) argv[argc++]=p; continue; }
            p++;
        }
        argv[argc]=NULL;
        if(seq(argv[0],"exit")) break;
        if(seq(argv[0],"help")) {
            for(const char* h="help echo ls cat cp rm grep vi ps ping ver clear exit\n";*h;h++) outb(0xE9,*h);
        } else if(seq(argv[0],"echo")) {
            for(int i=1;i<argc;i++) { for(const char* c=argv[i];*c;c++) outb(0xE9,*c); outb(0xE9,' '); }
            outb(0xE9,'\n');
        } else if(seq(argv[0],"ver")) {
            for(const char* v="NATKERNEL v3.0 + BusyBox 274K lines\n";*v;v++) outb(0xE9,*v);
        } else if(seq(argv[0],"clear")) {
            for(int i=0;i<30;i++) outb(0xE9,'\n');
        } else if(seq(argv[0],"ls")) {
            cmd_ls();
        } else if(seq(argv[0],"cat")) {
            cmd_cat(argc>1?argv[1]:"");
        } else if(seq(argv[0],"cp")) {
            cmd_cp(argc>1?argv[1]:"",argc>2?argv[2]:"");
        } else if(seq(argv[0],"rm")) {
            cmd_rm(argc>1?argv[1]:"");
        } else if(seq(argv[0],"grep")) {
            cmd_grep(argc>1?argv[1]:"",argc>2?argv[2]:"");
        } else if(seq(argv[0],"vi")) {
            editor_run();
        } else if(seq(argv[0],"ps")) {
            cmd_ps();
        } else if(seq(argv[0],"ping")) {
            cmd_ping(0);
        } else {
            for(const char* c=argv[0];*c;c++) outb(0xE9,*c);
            for(const char* nf=": not found\n";*nf;nf++) outb(0xE9,*nf);
        }
    }
}
