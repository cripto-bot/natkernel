/* PCIe Subsystem — N=5 IR kinds */
#include <natkernel/pcie.h>

#define PCI_MAX_BUS      256
#define PCI_MAX_DEV       32
#define PCI_MAX_FUNC       8
#define PCI_CONFIG_ADDR   0xCF8
#define PCI_CONFIG_DATA   0xCFC
#define PCI_VENDOR_ID     0x00
#define PCI_DEVICE_ID     0x02
#define PCI_COMMAND       0x04
#define PCI_STATUS        0x06
#define PCI_CLASS_REV     0x08
#define PCI_BAR0          0x10
#define PCI_IRQ_LINE      0x3C
#define PCI_MSI_CAP       0x05
#define PCI_MSIX_CAP      0x11
typedef struct { u16 vendor; u16 device; u16 cmd; u16 status; u8 class; u8 subclass; u8 prog_if; u8 rev; u8 irq; u32 bar[6]; } PCIDevice;
PCIDevice* pci_devices[PCI_MAX_BUS * PCI_MAX_DEV * PCI_MAX_FUNC];

static inline u32 pci_read(u8 bus, u8 dev, u8 func, u8 off) { u32 addr = 0x80000000 | (bus << 16) | (dev << 11) | (func << 8) | (off & 0xFC); outl(PCI_CONFIG_ADDR, addr); return inl(PCI_CONFIG_DATA); }
static inline void pci_write(u8 bus, u8 dev, u8 func, u8 off, u32 val) { outl(PCI_CONFIG_ADDR, 0x80000000 | (bus << 16) | (dev << 11) | (func << 8) | (off & 0xFC)); outl(PCI_CONFIG_DATA, val); }

PCIDevice* pci_find_device(u16 vendor, u16 device) {
    for (u32 b = 0; b < PCI_MAX_BUS; b++)
        for (u32 d = 0; d < PCI_MAX_DEV; d++)
            for (u32 f = 0; f < PCI_MAX_FUNC; f++) {
                u32 idx = b * PCI_MAX_DEV * PCI_MAX_FUNC + d * PCI_MAX_FUNC + f;
                if (pci_devices[idx] && pci_devices[idx]->vendor == vendor && pci_devices[idx]->device == device)
                    return pci_devices[idx];
            }
    return NULL;
}
void pci_enable_device(PCIDevice* dev) { u16 cmd = pci_read(dev->bus, dev->dev, dev->func, PCI_COMMAND) | 7; pci_write(dev->bus, dev->dev, dev->func, PCI_COMMAND, cmd); }
