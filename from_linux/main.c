/* NATKERNEL Main — FULL system test */
#include "../kernel.h"

static Process all_procs_array[MAX_PROCESSES];
Process* all_procs = all_procs_array;
Process* sched_procs(u32 i) { return (i < MAX_PROCESSES) ? &all_procs[i] : NULL; }

extern char __bss_start[];
extern char __bss_end[];

void debug(const char* s) { for (const char* c = s; *c; c++) outb(0xE9, *c); }
void debug_n(int n) { char buf[16]; int i = 0; if (n==0) { outb(0xE9,'0'); return; } while(n){buf[i++]='0'+n%10;n/=10;} while(i)outb(0xE9,buf[--i]); }

void test_a(void) { debug("[A]"); for(volatile int i=0;i<100000;i++); }
void test_b(void) { debug("[B]"); for(volatile int i=0;i<100000;i++); }

void kernel_main(void) {
    char* bss = __bss_start; char* bss_end = __bss_end;
    while (bss < bss_end) *bss++ = 0;
    
    debug("\n===== NATKERNEL v3.0 =====\n");
    
    /* Init subsystems */
    debug("[init] arch... "); arch_init(); debug("OK\n");
    debug("[init] memory... "); debug_n(get_free()); debug(" pages free\n");
    debug("[init] scheduler... "); sys_init(); debug("OK\n");
    debug("[init] fs... "); 
    u32 fd = vfs_open("/test", 4);
    if (fd) { vfs_write(fd, "HELLO", 5); vfs_close(fd); debug("wrote 5B\n"); }
    debug("[init] net... "); u32 s = socket_create(2,1); debug(s?"socket OK\n":"fail\n");
    debug("[init] usb... "); usb_init(); debug("OK\n");
    debug("[init] pci... "); pci_init(); debug("OK\n");
    debug("[init] crypto... "); crypto_init(); u32 r = rand_u32(); debug("RNG:"); debug_n(r%1000); debug("\n");
    
    /* Spawn test processes */
    debug("[sched] spawning 2 processes\n");
    sched_spawn(test_a);
    sched_spawn(test_b);
    
    /* Read back file */
    char buf[16];
    for(int i=0;i<16;i++) buf[i]=0;
    fd = vfs_open("/test", 0);
    if (fd) { vfs_read(fd, buf, 10); vfs_close(fd); debug("[fs] read: "); debug(buf); debug("\n"); }
    
    debug("[sched] running... ");
    
    /* Main loop with scheduler */
    for(int tick=0;;tick++) {
        sched_tick();
        if (tick % 5 == 0) debug(".");
        for(volatile u64 i = 0; i < 500000; i++) asm volatile("nop");
    }
}
