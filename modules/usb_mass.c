/* NATKERNEL usb_mass — N=4 IR kinds */
/* Specs: Generic specification */
#include "../kernel.h"

/* define */
#define USB_MASS_VERSION "0.1.0"

/* struct */
typedef struct { u32 version; void* data; } usb_mass_ctx;

/* inline */
static inline int usb_mass_init() { return 0; }

/* loop */
void usb_mass_scan() { for (u32 i = 0; i < 64; i++) { /* scan */ } }

/* if */
int usb_mass_ready() { usb_mass_ctx ctx; if (ctx.version) return 1; return 0; }

/* return */
void* usb_mass_get_data() { return NULL; }
