# ═══════════════════════════════════════════
# 2. CODE GENERATORS — Aligned structs + functions
# ═══════════════════════════════════════════
IR_KINDS = ['struct', 'define', 'inline', 'loop', 'if', 'return']

def gen_define(module):
    defs = {
        'usb': '''#define USB_MAX_DEVICES   128
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
#define USB_CLASS_HUB      0x09''',
        'tcpip': '''#define ETH_ALEN      6
#define IP_MAX_PACKET  65535
#define TCP_MAX_SEG    1460
#define MAX_SEG        1460
#define MAX_SOCKETS    1024
#define BACKLOG        128
#define SOCK_STREAM    1
#define AF_INET        2
#define IPPROTO_TCP    6
#define TCP_SYN        0x02
#define TCP_ACK        0x10
#define TCP_FIN        0x01
#define TCP_RST        0x04''',
        'smp': '''#define MAX_CPUS        64
#define PERCPU_OFFSET   0x1000
#define IPI_RESCHEDULE  0x02
#define IPI_CALL_FUNC   0x03''',
        'pcie': '''#define PCI_MAX_BUS      256
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
#define PCI_IRQ_LINE      0x3C''',
        'ext2': '''#define EXT2_SUPER_MAGIC  0xEF53
#define EXT2_BLOCK_SIZE    1024
#define EXT2_INODES_PER_BLOCK 8
#define EXT2_MAX_FILENAME  255
#define EXT2_NDIR_BLOCKS   12
#define EXT2_IND_BLOCK     13
#define EXT2_DIND_BLOCK    14
#define EXT2_TIND_BLOCK    15
#define EXT2_S_IFREG       0x8000
#define EXT2_S_IFDIR       0x4000
#define EXT2_ROOT_INO      2''',
    }
    return defs.get(module, '')

def gen_struct(module):
    structs = {
        'usb': '''typedef struct { u16 vendor; u16 product; u16 bcd; u8 cls; u8 subclass; u8 protocol; u8 max_packet; } USBDesc;
typedef struct { u8 addr; u8 config; USBDesc desc; void* driver; u8 endpoints[16]; u32 active; } USBDevice;
USBDevice* usb_devices[USB_MAX_DEVICES];''',
        'tcpip': '''typedef struct { u32 ip; u16 port; u32 peer_ip; u16 peer_port; u32 state; u32 seq; u32 ack; u32 rx_len; u8* rx_buf; } TCPSocket;
typedef struct { u32 src; u32 dst; u8 proto; u8 ttl; u16 id; u16 len; u16 checksum; } IPHeader;
TCPSocket* socket_table[MAX_SOCKETS];''',
        'pcie': '''typedef struct { u8 bus; u8 dev; u8 func; u16 vendor; u16 device; u16 cmd; u16 status; u8 cls; u8 subclass; u8 prog_if; u8 rev; u8 irq; u32 bar[6]; } PCIDevice;
PCIDevice* pci_devices[PCI_MAX_BUS * PCI_MAX_DEV * PCI_MAX_FUNC];''',
        'ext2': '''typedef struct { u32 inodes; u32 blocks; u32 r_blocks; u32 free_blocks; u32 free_inodes; u32 first_data; u32 log_block_size; u32 blocks_per_group; u32 inodes_per_group; u16 magic; u16 state; } Ext2Super;
typedef struct { u16 mode; u16 uid; u32 size; u32 atime; u32 mtime; u32 dtime; u16 gid; u16 links; u32 blocks; u32 block[15]; } Ext2Inode;
Ext2Super* ext2_super;''',
        'smp': '''typedef struct { u32 cpu_id; u32 state; void* gdt; void* idt; void* stack; u32 online; } CPU;
CPU percpu[MAX_CPUS];''',
    }
    return structs.get(module, '')

def gen_inline(module):
    inlines = {
        'usb': '''static inline void usb_writel(u32 addr, u32 val) { *(volatile u32*)addr = val; }
static inline u32 usb_readl(u32 addr) { return *(volatile u32*)addr; }
static inline void usb_reset_port(u32 port) { usb_writel(port + 0x10, 0x100); }
static inline int usb_wait_ready(u32 port) { for (int i = 0; i < 100000; i++) { if (usb_readl(port) & 1) return 1; } return 0; }''',
        'tcpip': '''static inline u16 ip_checksum(void* data, u32 len) { u32 sum = 0; u16* p = (u16*)data; for (u32 i = 0; i < len/2; i++) { sum += p[i]; if (sum > 0xFFFF) sum = (sum & 0xFFFF) + 1; } return (u16)~sum; }
static inline u32 tcp_checksum(TCPSocket* sk, void* data, u32 len) { u32 sum = sk->ip + sk->peer_ip + IPPROTO_TCP + len; return ip_checksum(data, len); }
static inline int socket_hash(u32 ip, u16 port) { return (ip ^ port) % MAX_SOCKETS; }''',
        'pcie': '''static inline u32 pci_read(u8 bus, u8 dev, u8 func, u8 off) { u32 addr = 0x80000000 | (bus << 16) | (dev << 11) | (func << 8) | (off & 0xFC); outl(PCI_CONFIG_ADDR, addr); return inl(PCI_CONFIG_DATA); }
static inline void pci_write(u8 bus, u8 dev, u8 func, u8 off, u32 val) { outl(PCI_CONFIG_ADDR, 0x80000000 | (bus << 16) | (dev << 11) | (func << 8) | (off & 0xFC)); outl(PCI_CONFIG_DATA, val); }''',
        'smp': '''static inline void send_ipi(u32 cpu, u32 vector) { *(volatile u32*)(0xFEE00000 + cpu*0x1000) = vector; }
static inline u32 get_cpu_id() { u32 id; asm volatile("movl %%gs:0, %0" : "=r"(id)); return id; }''',
    }
    return inlines.get(module, '')

def gen_loop(module):
    loops = {
        'usb': '''void usb_scan_bus() {
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
}''',
        'tcpip': '''void tcp_send(TCPSocket* sk, void* data, u32 len) {
    u8 buf[1500];
    IPHeader* ip = (IPHeader*)buf;
    ip->src = sk->ip; ip->dst = sk->peer_ip; ip->proto = IPPROTO_TCP;
    ip->ttl = 64; ip->len = len + 40;
    for (u32 i = 0; i < len; i += TCP_MAX_SEG) {
        u32 seg = (len - i > TCP_MAX_SEG) ? TCP_MAX_SEG : (len - i);
        ip->checksum = ip_checksum(ip, 20);
        sk->seq += seg;
    }
}
void ip_send(IPHeader* ip, u32 len) {}''',
        'smp': '''void smp_init() {
    for (u32 cpu = 0; cpu < MAX_CPUS; cpu++) {
        if (cpu == 0) { percpu[cpu].online = 1; continue; }
        percpu[cpu].cpu_id = cpu;
        percpu[cpu].stack = alloc_page();
        if (percpu[cpu].stack) { send_ipi(cpu, 0x40); percpu[cpu].online = 1; }
    }
}''',
        'ext2': '''void ext2_read_inode(u32 ino, Ext2Inode* inode) {
    u32 group = (ino - 1) / EXT2_INODES_PER_BLOCK;
    u32 index = (ino - 1) % EXT2_INODES_PER_BLOCK;
    u32 block = ext2_super->first_data + group * ext2_super->blocks_per_group;
    for (u32 i = 0; i < sizeof(Ext2Inode); i++) ((u8*)inode)[i] = block + i;
}
u32 ext2_read_file(u32 ino, void* buf, u32 size) {
    Ext2Inode inode; ext2_read_inode(ino, &inode);
    u32 read = 0;
    for (u32 i = 0; i < EXT2_NDIR_BLOCKS && read < size; i++) {
        u32 chunk = (size - read > EXT2_BLOCK_SIZE) ? EXT2_BLOCK_SIZE : (size - read);
        for (u32 j = 0; j < chunk; j++) ((u8*)buf)[read+j] = inode.block[i] + j;
        read += chunk;
    }
    return read;
}''',
    }
    return loops.get(module, '')

def gen_if(module):
    return {
        'usb': '''int usb_set_address(USBDevice* dev, u8 addr) {
    if (usb_wait_ready(dev->addr)) { dev->addr = addr; return 1; }
    return 0;
}
int usb_set_config(USBDevice* dev, u8 config) {
    if (usb_wait_ready(dev->addr)) { dev->config = config; return 1; }
    return 0;
}''',
        'tcpip': '''TCPSocket* tcp_accept(TCPSocket* sk) {
    if (sk == NULL || sk->state != 2) return NULL;
    u32 new_fd = socket_alloc(sk->ip, sk->peer_port);
    if (new_fd == 0) return NULL;
    TCPSocket* ns = socket_table[new_fd];
    ns->ip = sk->ip; ns->port = sk->peer_port;
    ns->peer_ip = sk->ip; ns->peer_port = sk->port;
    ns->state = 3; ns->seq = sk->ack;
    return ns;
}''',
        'ext2': '''int ext2_mount(void* disk) {
    ext2_super = (Ext2Super*)alloc_page();
    for (u32 i = 0; i < sizeof(Ext2Super); i++) ((u8*)ext2_super)[i] = ((u8*)disk)[i];
    if (ext2_super->magic != EXT2_SUPER_MAGIC) return -1;
    return 0;
}''',
        'smp': '''int cpu_online(u32 cpu) {
    if (cpu >= MAX_CPUS) return 0;
    if (percpu[cpu].online == 0) return 0;
    return 1;
}''',
    }.get(module, '')

def gen_return(module):
    return {
        'usb': '''USBDevice* usb_find_device(u16 vendor, u16 product) {
    for (int i = 0; i < USB_MAX_DEVICES; i++)
        if (usb_devices[i] && usb_devices[i]->desc.vendor == vendor)
            return usb_devices[i];
    return NULL;
}''',
        'tcpip': '''TCPSocket* socket_lookup(u32 ip, u16 port) {
    u32 idx = socket_hash(ip, port);
    return socket_table[idx];
}
u32 socket_alloc(u32 ip, u16 port) {
    for (u32 i = 0; i < MAX_SOCKETS; i++) {
        if (socket_table[i] == NULL) {
            socket_table[i] = (TCPSocket*)alloc_page();
            socket_table[i]->ip = ip; socket_table[i]->port = port;
            socket_table[i]->state = 1;
            return i;
        }
    }
    return 0;
}''',
        'pcie': '''PCIDevice* pci_find_device(u16 vendor, u16 device) {
    for (u32 i = 0; i < PCI_MAX_BUS * PCI_MAX_DEV * PCI_MAX_FUNC; i++)
        if (pci_devices[i] && pci_devices[i]->vendor == vendor)
            return pci_devices[i];
    return NULL;
}
void pci_enable_device(PCIDevice* dev) { pci_write(dev->bus, dev->dev, dev->func, PCI_COMMAND, pci_read(dev->bus, dev->dev, dev->func, PCI_COMMAND) | 7); }''',
    }.get(module, '')

# ═══════════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════════
KERNEL_MODULES = {
    'usb':    ('{define}\n{struct}\n{inline}\n{loop}\n{if}\n{return}', ['struct','define','inline','if','loop','return']),
    'tcpip':  ('{define}\n{struct}\n{inline}\n{loop}\n{if}\n{return}', ['struct','define','inline','loop','if','return']),
    'smp':    ('{define}\n{struct}\n{inline}\n{loop}\n{if}', ['struct','define','inline','if','loop']),
    'pcie':   ('{define}\n{struct}\n{inline}\n{return}\n{if}', ['struct','define','inline','if','return']),
    'ext2':   ('{define}\n{struct}\n{inline}\n{loop}\n{if}\n{return}', ['struct','define','inline','loop','if','return']),
}

if __name__ == '__main__':
    import os; os.makedirs('modules', exist_ok=True)
    generators = {'define': gen_define, 'struct': gen_struct, 'inline': gen_inline, 'loop': gen_loop, 'if': gen_if, 'return': gen_return}
    total = 0
    for name, (template, kinds) in KERNEL_MODULES.items():
        filled = {k: generators.get(k, lambda x:'')(name) for k in IR_KINDS}
        code = '/* ' + name.upper() + ' — N=' + str(len(kinds)) + ' */\n#include "../kernel.h"\n\n' + template.format(**filled)
        path = f'modules/{name}.c'
        with open(path, 'w') as f: f.write(code.strip()+'\n')
        lines = len(code.splitlines())
        total += lines
        print(f'{name:8s}: {lines:>4} lines  N={len(kinds)}  kinds={kinds}')
    print(f'\nTOTAL: {total} lines generated')
