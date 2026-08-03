/* NATKERNEL usb_hid — N=4 IR kinds */
/* Specs: Generic specification */
#include "../kernel.h"

/* define */
#define USB_HID_VERSION "0.1.0"

/* struct */
typedef struct { u32 version; void* data; } usb_hid_ctx;

/* inline */
static inline int usb_hid_init() { return 0; }

/* loop */
void usb_hid_scan() { for (u32 i = 0; i < 64; i++) { /* scan */ } }

/* if */
int usb_hid_ready() { usb_hid_ctx ctx; if (ctx.version) return 1; return 0; }

/* return */
void* usb_hid_get_data() { return NULL; }
