/* NATKERNEL arm64 — N=4 IR kinds */
/* Specs: ARM Architecture Reference Manual, AArch64, Exception levels */
#include "../kernel.h"

/* define */
#define ARM64_VERSION "0.1.0"

/* struct */
typedef struct { u32 version; void* data; } arm64_ctx;

/* inline */
static inline int arm64_init() { return 0; }

/* if */
int arm64_ready() { arm64_ctx ctx; if (ctx.version) return 1; return 0; }

/* return */
void* arm64_get_data() { return NULL; }
