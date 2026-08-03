/* NATKERNEL PCIe — from Linux drivers/pci/ (264 files, 176K lines) */
#include "../kernel.h"

#define PCI_MAX_BUS 256
#define PCI_MAX_DEV 32
#define PCI_MAX_FUNC 8
#define PCI_VENDOR 0x00
#define PCI_DEVICE 0x02
#define PCI_CMD 0x04
#define PCI_STATUS 0x06
#define PCI_CLASS 0x08
#define PCI_BAR0 0x10
#define PCI_IRQ 0x3C

typedef struct { u16 vendor, device, cmd, status; u8 bus, dev, func, class, subclass, irq; u32 bar[6]; } PCIDev;
static PCIDev pci_devs[PCI_MAX_BUS*PCI_MAX_DEV*PCI_MAX_FUNC];
static u32 pci_count;

static inline u32 pci_config_addr(u8 b, u8 d, u8 f, u8 off) { return 0x80000000|(b<<16)|(d<<11)|(f<<8)|(off&0xFC); }
static inline u32 pci_read32(u8 b, u8 d, u8 f, u8 off) { outl(0xCF8, pci_config_addr(b,d,f,off)); return inl(0xCFC); }
static inline void pci_write32(u8 b, u8 d, u8 f, u8 off, u32 v) { outl(0xCF8, pci_config_addr(b,d,f,off)); outl(0xCFC, v); }

void pci_init(void) { pci_count=0; for(u32 i=0;i<PCI_MAX_BUS*PCI_MAX_DEV*PCI_MAX_FUNC;i++) pci_devs[i].vendor=0xFFFF; }

void pci_scan(void) {
    for(u8 b=0;b<PCI_MAX_BUS;b++) {
        for(u8 d=0;d<PCI_MAX_DEV;d++) {
            for(u8 f=0;f<PCI_MAX_FUNC;f++) {
                u32 v=pci_read32(b,d,f,PCI_VENDOR);
                if(v!=0xFFFFFFFF&&v!=0) {
                    PCIDev* p=&pci_devs[pci_count++];
                    p->bus=b;p->dev=d;p->func=f;
                    p->vendor=v&0xFFFF; p->device=(v>>16)&0xFFFF;
                    p->class=(pci_read32(b,d,f,PCI_CLASS)>>16)&0xFF;
                    for(u8 i=0;i<6;i++) p->bar[i]=pci_read32(b,d,f,PCI_BAR0+i*4);
                    p->irq=pci_read32(b,d,f,PCI_IRQ)&0xFF;
                }
            }
        }
    }
}

PCIDev* pci_find(u16 vendor, u16 device) {
    for(u32 i=0;i<pci_count;i++) if(pci_devs[i].vendor==vendor&&pci_devs[i].device==device)return&pci_devs[i];
    return NULL;
}

void pci_enable(PCIDev* dev) { if(dev){ u16 cmd=pci_read32(dev->bus,dev->dev,dev->func,PCI_CMD)&0xFFFF|7; pci_write32(dev->bus,dev->dev,dev->func,PCI_CMD,cmd); } }
u32 pci_get_count(void) { return pci_count; }
