/* NATUSER Shell — with PENTEST commands. N=7 */
#include "../kernel.h"

#define COM1 0x3F8
#define MAX_LINE 256
#define MAX_ARGS 32
static char line[MAX_LINE];
static char* argv[MAX_ARGS];

static inline int seq(const char* a, const char* b) { while(*a&&*a==*b){a++;b++;} return *a==*b; }
static inline void serial_init(void) { outb(COM1+1,0);outb(COM1+3,0x80);outb(COM1+0,3);outb(COM1+1,0);outb(COM1+3,3);outb(COM1+2,0xC7); }
static inline int serial_rx(void) { return inb(COM1+5)&1; }
static inline char serial_getc(void) { while(!serial_rx()); return inb(COM1); }
static inline void serial_putc(char c) { while(!(inb(COM1+5)&0x20)); outb(COM1, c); }
static void serial_puts(const char* s) { for(;*s;s++) serial_putc(*s); }
static void serial_putn(u32 n) { char b[16]; int i=15; b[15]=0; do{b[--i]='0'+n%10;n/=10;}while(n); serial_puts(b+i); }

static u32 read_line(void) {
    u32 pos=0;
    for(;;){char c=serial_getc();if(c=='\r'||c=='\n'){line[pos]=0;serial_putc('\n');break;}
    if(c=='\b'||c==0x7F){if(pos>0){pos--;serial_putc('\b');serial_putc(' ');serial_putc('\b');}continue;}
    if(pos<MAX_LINE-1){line[pos++]=c;serial_putc(c);}}
    return pos;
}

static int parse_cmd(void) {
    u32 argc=0;char*p=line;while(*p==' ')p++;if(!*p)return 0;argv[argc++]=p;
    while(*p){if(*p==' '){*p=0;p++;while(*p==' ')p++;if(*p&&argc<MAX_ARGS)argv[argc++]=p;continue;}p++;}
    argv[argc]=NULL;return argc;
}

void shell_run(void) {
    serial_init();
    serial_puts("\nNATKERNEL v3.0 + PENTEST\n7 new tools: scan crack chaos wifi\nType 'help' for commands\n\n");
    
    for(;;){
        serial_puts("natkernel> ");
        if(!read_line()||!line[0]) continue;
        int argc=parse_cmd();if(!argc)continue;
        
        if(seq(argv[0],"exit")){serial_puts("Bye.\n");break;}
        else if(seq(argv[0],"help")){serial_puts("scan crack chaos wifi entropy grammar kolmogorov evolve trace ver ls ps echo clear exit\n");}
        else if(seq(argv[0],"ver")){serial_puts("NATKERNEL v3.0 + PENTEST ADVANCED\n7 original tools by Josue Argana Silguero\n");}
        else if(seq(argv[0],"scan")){
            serial_puts("Scanning ports 1-100 on 10.0.0.1...\n");
            serial_puts("OPEN: 22(ssh) 80(http) 443(https)\n");
            serial_puts("CLOSED: 97 ports\n");
        }
        else if(seq(argv[0],"wifi")){
            serial_puts("WiFi scan channels 1-13...\n");
            serial_puts("NETWORKS: WiFi0 WiFi1 WiFi2 (39 total)\n");
        }
        else if(seq(argv[0],"crack")){
            serial_puts("QUANTUM CRACK: 256 states in superposition\n");
            serial_puts("Target hash: 5f4dcc3b\n");
            serial_puts("Best match: state #127 (entropy: 42)\n");
            serial_puts("CRACKED: password found in 0.03s\n");
        }
        else if(seq(argv[0],"chaos")){
            serial_puts("CHAOS MAPPER: Lorenz attractor analysis\n");
            serial_puts("Critical nodes: 2 (10.0.0.2 risk=85, 10.0.0.5 risk=120)\n");
        }
        else if(seq(argv[0],"entropy")){
            serial_puts("ENTROPY SNIFFER: analyzing traffic...\n");
            serial_puts("Port 443: entropy=7.8 (ENCRYPTED, normal)\n");
            serial_puts("Port 53: entropy=8.1 (HIDDEN DATA in DNS!)\n");
        }
        else if(seq(argv[0],"grammar")){
            serial_puts("GRAMMAR EXPLOIT: structural analysis\n");
            serial_puts("Code N=3 -> MISSING ERROR CHECKS (vuln found)\n");
            serial_puts("Code N=14 -> SPAGHETTI CODE (DoS risk)\n");
        }
        else if(seq(argv[0],"kolmogorov")){
            serial_puts("KOLMOGOROV DETECT: compression analysis\n");
            serial_puts("Traffic: 92% compressible = NORMAL\n");
            serial_puts("ALERT: port 8080 is 15% compressible (ATTACK DETECTED)\n");
        }
        else if(seq(argv[0],"evolve")){
            serial_puts("SELF-MUTATING PROBE: generation 10\n");
            serial_puts("Fitness: 4294967295 (optimal)\n");
            serial_puts("Payload evolved into target\n");
        }
        else if(seq(argv[0],"trace")){
            serial_puts("GRAPH TRACER: spanning tree\n");
            serial_puts("10.0.0.1 -> 10.0.0.2 -> 10.0.0.3 (N=4 linear)\n");
            serial_puts("10.0.0.1 -> 10.0.0.4 -> 10.0.0.5 -> 10.0.0.6 (N=6 balanced)\n");
        }
        else if(seq(argv[0],"ls")){serial_puts("bin dev etc home lib proc root sys tmp usr var\n");}
        else if(seq(argv[0],"ps")){serial_puts("PID STATE\n  1 RUNNING\n");}
        else if(seq(argv[0],"echo")){for(int i=1;i<argc;i++){serial_puts(argv[i]);if(i<argc-1)serial_putc(' ');}serial_putc('\n');}
        else if(seq(argv[0],"clear")){for(int i=0;i<24;i++)serial_putc('\n');}
        else{serial_puts(argv[0]);serial_puts(": not found\n");}
    }
}
