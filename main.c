/* NATKERNEL Main — Boot and init */
#include "kernel.h"

/* IR-extern: Multiboot info */
extern u32 __bss_start;
extern u32 __bss_end;

/* IR-loop: Clear BSS */
static void clear_bss() {
    u64* start = (u64*)&__bss_start;
    u64* end = (u64*)&__bss_end;
    for (u64* p = start; p < end; p++) *p = 0;
}

/* IR-loop: Test processes */
static void test_process_a() {
    const char* msg = "[PID-A] Running task A... ";
    syscall_dispatch(SYS_WRITE, (u64)msg, 25, NULL);
}

static void test_process_b() {
    const char* msg = "[PID-B] Computing result... ";
    syscall_dispatch(SYS_WRITE, (u64)msg, 25, NULL);
}

/* Main entry */
void kernel_main() {
    clear_bss();
    sys_init();
    
    /* Boot banner */
    const char* banner = "\n===== NATKERNEL v" NAT_VERSION " =====\n"
    "Universal Grammar Kernel (N=7)\n"
    "IR: struct define typedef inline loop if return\n"
    "Author: Josue Argana Silguero\n"
    "License: MII Open v1.0\n"
    "========================================\n\n";
    syscall_dispatch(SYS_WRITE, (u64)banner, 0, NULL);
    
    /* Keyboard + FS test */
    const char* prompt = "$ ";
    syscall_dispatch(SYS_WRITE, (u64)prompt, 2, NULL);
    
    u32 fd = fs_create("/etc/motd", 64);
    const char* motd = "Welcome to NATKERNEL — the kernel designed by universal grammar.";
    fs_write(fd, motd, 64);
    
    char buf[65];
    fs_read(fd, buf, 64);
    buf[64] = 0;
    syscall_dispatch(SYS_WRITE, (u64)buf, 64, NULL);
    
    /* Spawn test processes */
    sched_spawn(test_process_a);
    sched_spawn(test_process_b);
    
    /* Main kernel loop */
    for (;;) {
        sched_tick();
        for (volatile u64 i = 0; i < 1000000; i++) asm volatile("nop");
    }
}
