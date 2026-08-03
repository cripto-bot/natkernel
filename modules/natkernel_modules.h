/* NATKERNEL Module Headers — Auto-generated */
#ifndef NATKERNEL_MODULES_H
#define NATKERNEL_MODULES_H
#include "../kernel.h"

/* USB */
typedef struct { u16 vendor; u16 product; u16 bcd; u8 class; u8 subclass; u8 protocol; u8 max_packet; } USBDesc;
typedef struct { u8 addr; u8 config; USBDesc desc; void* driver; u8 endpoints[16]; u32 active; } USBDevice;
USBDevice* usb_find_device(u16 vendor, u16 product);
void usb_scan_bus();
int usb_set_address(USBDevice* dev, u8 addr);

/* TCP/IP */
typedef struct { u32 src_ip; u32 dst_ip; u16 src_port; u16 dst_port; u32 seq; u32 ack; u8 flags; u16 window; u8* data; u32 len; } TCPPacket;
typedef struct { u32 ip; u16 port; u32 state; u32 seq; u32 ack; } TCPSocket;
u32 tcp_send(u32 sock, void* data, u32 len);
u32 tcp_accept(u32 listen_fd);

/* PCIe */
typedef struct { u16 vendor; u16 device; u16 cmd; u16 status; u8 class; u8 subclass; u8 irq; u32 bar[6]; } PCIDevice;
PCIDevice* pci_find_device(u16 vendor, u16 device);
void pci_enable_device(PCIDevice* dev);

/* SMP */
void smp_init();
int cpu_online(u32 cpu);

/* ext2 */
int ext2_mount(void* disk);
u32 ext2_read_file(u32 ino, void* buf, u32 size);

#endif
