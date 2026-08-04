/* USB — N=6 */
#include "../kernel.h"

#define USB_MAX_DEVICES   128
#define USB_DESC_SIZE     18
#define USB_EP_MAX_PACKET 1024
#define USB_CTRL_REQUEST   0x80
#define USB_ENDPOINT_IN    0x80
#define USB_ENDPOINT_OUT   0x00
#define USB_DEV_DESCRIPTOR 0x01
#define USB_SET_ADDRESS    0x05
#define USB_SET_CONFIG     0x09
#define USB_CLASS_HID      0x03
#define USB_CLASS_MASS     0x08
#define USB_CLASS_HUB      0x09
typedef struct { u16 vendor; u16 product; u16 bcd; u8 cls; u8 subclass; u8 protocol; u8 max_packet; } USBDesc;
typedef struct { u8 addr; u8 config; USBDesc desc; void* driver; u8 endpoints[16]; u32 active; } USBDevice;
USBDevice* usb_devices[USB_MAX_DEVICES];
static inline void usb_writel(u32 addr, u32 val) { *(volatile u32*)addr = val; }
static inline u32 usb_readl(u32 addr) { return *(volatile u32*)addr; }
static inline void usb_reset_port(u32 port) { usb_writel(port + 0x10, 0x100); }
static inline int usb_wait_ready(u32 port) { for (int i = 0; i < 100000; i++) { if (usb_readl(port) & 1) return 1; } return 0; }
void usb_scan_bus() {
    for (u32 port = 0; port < USB_MAX_DEVICES; port++) {
        usb_reset_port(port);
        if (usb_wait_ready(port)) {
            USBDevice* dev = (USBDevice*)alloc_page();
            dev->addr = port;
            dev->config = 1;
            usb_devices[port] = dev;
            usb_get_descriptor(dev);
        }
    }
}
void usb_get_descriptor(USBDevice* dev) {
    for (u32 i = 0; i < USB_DESC_SIZE; i++) ((u8*)&dev->desc)[i] = inb(0x60 + i);
}
int usb_set_address(USBDevice* dev, u8 addr) {
    if (usb_wait_ready(dev->addr)) { dev->addr = addr; return 1; }
    return 0;
}
int usb_set_config(USBDevice* dev, u8 config) {
    if (usb_wait_ready(dev->addr)) { dev->config = config; return 1; }
    return 0;
}
USBDevice* usb_find_device(u16 vendor, u16 product) {
    for (int i = 0; i < USB_MAX_DEVICES; i++)
        if (usb_devices[i] && usb_devices[i]->desc.vendor == vendor)
            return usb_devices[i];
    return NULL;
}
void usb_init(void) {}
