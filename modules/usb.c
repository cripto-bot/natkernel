/* USB Subsystem — N=6 IR kinds */
#include <natkernel/usb.h>

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
typedef struct { u16 vendor; u16 product; u16 bcd; u8 class; u8 subclass; u8 protocol; u8 max_packet; } USBDesc;
typedef struct { u8 addr; u8 config; USBDesc desc; void* driver; u8 endpoints[16]; u32 active; } USBDevice;
typedef struct { u8 type; u8 request; u16 value; u16 index; u16 len; } __attribute__((packed)) USBRequest;
USBDevice* usb_devices[USB_MAX_DEVICES];


static inline void usb_writel(u32 addr, u32 val) { *(volatile u32*)addr = val; }
static inline u32 usb_readl(u32 addr) { return *(volatile u32*)addr; }
static inline void usb_reset_port(u32 port) { usb_writel(port + 0x10, 0x100); }
static inline int usb_wait_ready(u32 port) { for (int i = 0; i < 100000; i++) { if (usb_readl(port) & 1) return 1; } return 0; }
static inline void usb_setup_packet(u8 ep, u8 type, u8 req, u16 val) { USBRequest r = {type, req, val, 0, 0}; usb_writel(ep, *(u32*)&r); }
void usb_scan_bus() {
    for (u32 port = 0; port < USB_MAX_DEVICES; port++) {
        usb_reset_port(port);
        if (usb_wait_ready(port)) {
            USBDevice* dev = (USBDevice*)alloc_page();
            dev->addr = port;
            dev->config = 1;
            usb_devices[port] = dev;
            usb_get_descriptor(dev);
            usb_set_address(dev, port + 1);
            usb_set_config(dev, 1);
        }
    }
}
void usb_get_descriptor(USBDevice* dev) {
    usb_setup_packet(0, USB_DEV_DESCRIPTOR, USB_CTRL_REQUEST, 0);
    for (u32 i = 0; i < USB_DESC_SIZE; i++) ((u8*)&dev->desc)[i] = inb(0x60 + i);
}
void usb_register_driver(void* driver, u8 class) {
    for (u32 i = 0; i < USB_MAX_DEVICES; i++) {
        if (usb_devices[i] && usb_devices[i]->desc.class == class)
            usb_devices[i]->driver = driver;
    }
}
int usb_set_address(USBDevice* dev, u8 addr) {
    usb_setup_packet(0, 0x00, USB_SET_ADDRESS, addr);
    if (usb_wait_ready(dev->addr)) { dev->addr = addr; return 1; }
    return 0;
}
int usb_set_config(USBDevice* dev, u8 config) {
    usb_setup_packet(0, 0x00, USB_SET_CONFIG, config);
    if (usb_wait_ready(dev->addr)) { dev->config = config; return 1; }
    return 0;
}
int usb_claim_device(u32 bus, u32 dev_id) {
    if (bus >= USB_MAX_DEVICES) return 0;
    if (usb_devices[bus] == NULL) return 0;
    return usb_devices[bus]->config ? 1 : 0;
}
USBDevice* usb_find_device(u16 vendor, u16 product) {
    for (int i = 0; i < USB_MAX_DEVICES; i++)
        if (usb_devices[i] && usb_devices[i]->desc.vendor == vendor && usb_devices[i]->desc.product == product)
            return usb_devices[i];
    return NULL;
}
int usb_attach_driver(u32 dev_id, void* driver) {
    if (usb_devices[dev_id]) { usb_devices[dev_id]->driver = driver; return 1; }
    return 0;
}
