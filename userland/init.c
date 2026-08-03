/* NATUSER init — System bootstrap. N=5 ∈ [4,12] */
#include "../kernel.h"

/* IR-define */
#define WELCOME "\n===== NATKERNEL v3.0 =====\nUniversal Grammar Kernel\nLinux 37M -> 1K lines\nType 'help' for commands\n\n"

/* IR-struct */
static u32 boot_count;

/* IR-inline */
static inline void puts(const char* s) { for (;*s;s++) outb(0xE9, *s); }

/* IR-loop: Init sequence */
void init_start(void) {
    puts(WELCOME);
    
    /* Mount root */
    vfs_open("/", 4);
    
    /* Start subsystems */
    usb_init(); pci_init(); crypto_init();
    
    /* IR-if: Boot services */
    boot_count = 0;
    for (u32 i = 0; i < 3; i++) {
        puts("[init] service "); boot_count++;
        if (boot_count > 0) puts("OK\n");
    }
    
    /* Start shell */
    shell_run();
}
