#include "../kernel.h"
void sys_init(void) {}
u64 syscall_dispatch(u64 num, u64 a1, u64 a2, u64 a3) { (void)num;(void)a1;(void)a2;(void)a3; return 0; }
