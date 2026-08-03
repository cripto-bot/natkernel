/* NATKERNEL v3.0 Main — Integrated kernel + userland */
#include "../kernel.h"

static Process all_procs_array[MAX_PROCESSES];
Process* all_procs = all_procs_array;
Process* sched_procs(u32 i) { return (i < MAX_PROCESSES) ? &all_procs[i] : NULL; }

void debug(const char* s) { for (const char* c = s; *c; c++) outb(0xE9, *c); }

void kernel_main(void) {
    extern char __bss_start[], __bss_end[];
    char* b = __bss_start; char* be = __bss_end;
    while (b < be) *b++ = 0;

    debug("\n===== NATKERNEL v3.0 + NATUSER =====\n");
    
    /* Init subsystems */
    debug("[init] arch... "); arch_init(); debug("OK\n");
    debug("[init] memory... "); debug("OK\n");
    debug("[init] scheduler... "); debug("OK\n");
    debug("[init] fs... "); vfs_open("/", 4); debug("OK\n");
    debug("[init] usb... "); usb_init(); debug("OK\n");
    debug("[init] pci... "); pci_init(); debug("OK\n");
    debug("[init] crypto... "); crypto_init(); debug("OK\n");
    
    debug("\nStarting NATUSER shell...\n\n");
    shell_run();
    
    for(;;) asm volatile("hlt");
}
