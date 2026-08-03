"""
NATKERNEL MASSIVE EXPANSION — Auto-generate all subsystems.
interrupts, console, elf, ipc, crypto, security, power
All following N=7 IR kinds.
"""
import os

SUBSYSTEMS = {
    'interrupts': {
        'define': '''#define IDT_SIZE 256
#define IRQ_BASE 32
#define IRQ_TIMER 0
#define IRQ_KBD 1
#define IRQ_MOUSE 12
#define IRQ_ATA_PRIMARY 14
#define IRQ_ATA_SECONDARY 15
#define IRQ_SYSCALL 0x80
#define PAGE_FAULT 14
#define GP_FAULT 13
#define DOUBLE_FAULT 8''',
        'struct': '''typedef struct { u16 offset_low; u16 selector; u8 ist; u8 type_attr; u16 offset_mid; u32 offset_high; u32 reserved; } __attribute__((packed)) IDTEntry;
typedef struct { u64 r15,r14,r13,r12,r11,r10,r9,r8,rsi,rdi,rbp,rdx,rcx,rbx,rax; u64 int_no,err_code,rip,cs,rflags,rsp,ss; } IntFrame;''',
        'inline': '''static inline void lidt(IDTEntry* base, u16 size) { struct { u16 limit; u64 base; } __attribute__((packed)) idtr = {size-1,(u64)base}; asm volatile("lidt %0"::"m"(idtr)); }
static inline void sti() { asm volatile("sti"); }
static inline void cli() { asm volatile("cli"); }''',
        'loop': '''void init_idt() { for (u32 i = 0; i < IDT_SIZE; i++) { set_idt_gate(i, (u64)isr_stub, 0x08, 0x8E); } }''',
        'if': '''void isr_handler(IntFrame* f) {
    if (f->int_no == IRQ_TIMER) { sched_tick(); }
    if (f->int_no == IRQ_KBD) { u8 sc = inb(0x60); kb_handler(sc); }
    if (f->int_no == IRQ_MOUSE) { u8 d = inb(0x60); }
    if (f->int_no == IRQ_SYSCALL) { f->rax = syscall_dispatch(f->rax, f->rdi, f->rsi, f->rdx); }
    if (f->int_no == PAGE_FAULT) { kernel_panic("Page Fault"); }
    if (f->int_no == GP_FAULT) { kernel_panic("GP Fault"); }
    if (f->int_no == DOUBLE_FAULT) { kernel_panic("Double Fault"); }
}''',
        'return': '''void kernel_panic(const char* msg) { syscall_dispatch(SYS_WRITE, (u64)"PANIC: ", 7, NULL); syscall_dispatch(SYS_WRITE, (u64)msg, 0, NULL); while(1) asm volatile("hlt"); }
void set_idt_gate(u32 n, u64 handler, u16 sel, u8 flags) { idt[n].offset_low = handler & 0xFFFF; idt[n].selector = sel; idt[n].ist = 0; idt[n].type_attr = flags; idt[n].offset_mid = (handler>>16)&0xFFFF; idt[n].offset_high = (handler>>32)&0xFFFFFFFF; }''',
    },
    'console': {
        'define': '''#define CONSOLE_WIDTH 80
#define CONSOLE_HEIGHT 25
#define VGA_ADDR 0xB8000''',
        'struct': '''typedef struct { u32 x,y; u16* buffer; u8 color; } Console;''',
        'inline': '''static inline u16 vga_entry(char c, u8 fg, u8 bg) { return (u16)c | ((u16)(fg | bg<<4) << 8); }
static inline void console_putchar(char c) { u16* vga = (u16*)VGA_ADDR; if (c == '\\n') { console.x = 0; console.y++; } else { vga[console.y*CONSOLE_WIDTH+console.x] = vga_entry(c,7,0); if (++console.x >= CONSOLE_WIDTH) { console.x=0; console.y++; } } }''',
        'loop': '''void console_clear() { u16* vga = (u16*)VGA_ADDR; for (u32 i = 0; i < CONSOLE_WIDTH*CONSOLE_HEIGHT; i++) vga[i] = vga_entry(' ', 7, 0); console.x = 0; console.y = 0; }''',
        'if': '''void console_write(const char* s) { while(*s) { if (*s == '\\n') { console.x=0; console.y++; s++; } else { console_putchar(*s++); } } ; if (console.y >= CONSOLE_HEIGHT) { for (u32 i=0;i<CONSOLE_WIDTH*(CONSOLE_HEIGHT-1);i++) ((u16*)VGA_ADDR)[i]=((u16*)VGA_ADDR)[i+CONSOLE_WIDTH]; console.y--; } }''',
    },
    'elf': {
        'define': '''#define ELF_MAGIC 0x464C457F
#define ELF_PT_LOAD 1
#define PF_X 1
#define PF_W 2
#define PF_R 4''',
        'struct': '''typedef struct { u32 magic; u8 elf[12]; u16 type; u16 machine; u32 version; u64 entry; u64 phoff; u64 shoff; u32 flags; u16 ehsize; u16 phentsize; u16 phnum; u16 shentsize; u16 shnum; u16 shstrndx; } Elf64Header;
typedef struct { u32 type; u32 flags; u64 offset; u64 vaddr; u64 paddr; u64 filesz; u64 memsz; u64 align; } Elf64ProgHeader;''',
        'inline': '''static inline int elf_check(Elf64Header* h) { return h->magic == ELF_MAGIC && (h->machine == 0x3E || h->machine == 0xB7); }''',
        'loop': '''int elf_load(void* data, u64* entry) { Elf64Header* eh = (Elf64Header*)data; if (!elf_check(eh)) return 0; for (u16 i = 0; i < eh->phnum; i++) { Elf64ProgHeader* ph = (Elf64ProgHeader*)((u8*)data + eh->phoff + i*eh->phentsize); if (ph->type == ELF_PT_LOAD) { for (u64 j = 0; j < ph->memsz; j += PAGE_SIZE) { u64 page = alloc_page(); map_page(ph->vaddr+j, page, PAGE_PRESENT|PAGE_WRITABLE|PAGE_USER); } } } *entry = eh->entry; return 1; }''',
        'if': '''int exec_elf(const char* path) { u32 fd = fs_open(path); if (fd == 0) return -1; void* buf = (void*)alloc_page(); fs_read(fd, buf, PAGE_SIZE); u64 entry; if (elf_load(buf, &entry)) { Process* p = sched_current(); p->ctx.rip = entry; return 0; } return -2; }''',
    },
    'ipc': {
        'define': '''#define SIGKILL 9
#define SIGTERM 15
#define SIGINT 2
#define PIPE_SIZE 4096
#define MAX_PIPES 64''',
        'struct': '''typedef struct { u8 buf[PIPE_SIZE]; u32 head,tail; u32 readers,writers; } Pipe;''',
        'inline': '''static inline int pipe_full(Pipe* p) { return ((p->tail+1) % PIPE_SIZE) == p->head; }
static inline int pipe_empty(Pipe* p) { return p->head == p->tail; }''',
        'loop': '''u32 pipe_read(Pipe* p, void* buf, u32 len) { u32 n = 0; for (u32 i = 0; i < len && !pipe_empty(p); i++) { ((u8*)buf)[i] = p->buf[p->tail]; p->tail = (p->tail+1) % PIPE_SIZE; n++; } return n; }''',
        'if': '''u32 pipe_write(Pipe* p, const void* buf, u32 len) { u32 n = 0; for (u32 i = 0; i < len && !pipe_full(p); i++) { p->buf[p->head] = ((u8*)buf)[i]; p->head = (p->head+1) % PIPE_SIZE; n++; } return n; }''',
        'return': '''Pipe* pipe_create() { for (u32 i = 0; i < MAX_PIPES; i++) { if (pipes[i].readers == 0) { pipes[i].head = 0; pipes[i].tail = 0; pipes[i].readers = 1; return &pipes[i]; } } return NULL; }''',
    },
    'crypto': {
        'define': '''#define SHA256_OUTPUT 32
#define ED25519_KEY 32''',
        'inline': '''static inline u32 rotr32(u32 x, u32 n) { return (x>>n)|(x<<(32-n)); }
static inline u32 swap32(u32 x) { return ((x>>24)&0xff)|((x<<8)&0xff0000)|((x>>8)&0xff00)|((x<<24)&0xff000000); }''',
        'loop': '''void sha256(const u8* d, u32 len, u8* out) { u32 h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}; u32 k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2}; for (u32 i=0;i<len/64;i++) { const u8* b=d+i*64; u32 w[64]; for (u32 j=0;j<16;j++) w[j]=(b[j*4]<<24)|(b[j*4+1]<<16)|(b[j*4+2]<<8)|b[j*4+3]; for (u32 j=16;j<64;j++) { u32 s0=rotr32(w[j-15],7)^rotr32(w[j-15],18)^(w[j-15]>>3); u32 s1=rotr32(w[j-2],17)^rotr32(w[j-2],19)^(w[j-2]>>10); w[j]=w[j-16]+s0+w[j-7]+s1; } u32 a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],h2=h[7]; for (u32 j=0;j<64;j++) { u32 S1=rotr32(e,6)^rotr32(e,11)^rotr32(e,25); u32 ch=(e&f)^((~e)&g); u32 t1=h2+S1+ch+k[j]+w[j]; u32 S0=rotr32(a,2)^rotr32(a,13)^rotr32(a,22); u32 maj=(a&b)^(a&c)^(b&c); u32 t2=S0+maj; h2=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2; } h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=h2; } for (u32 j=0;j<8;j++) { out[j*4]=h[j]>>24;out[j*4+1]=(h[j]>>16)&0xFF;out[j*4+2]=(h[j]>>8)&0xFF;out[j*4+3]=h[j]&0xFF; } }''',
        'if': '''u32 random_u32() { static u64 seed = 123456789; seed = seed * 6364136223846793005ULL + 1442695040888963407ULL; return (u32)(seed >> 32); }''',
        'return': '''void random_bytes(u8* buf, u32 len) { for (u32 i = 0; i < len; i += 4) { u32 r = random_u32(); for (u32 j = 0; j < 4 && i+j < len; j++) buf[i+j] = (u8)(r >> (j*8)); } }''',
    },
    'security': {
        'define': '''#define MAX_USERS 64
#define MAX_GROUPS 32
#define ROOT_UID 0
#define S_IRWXU 0700
#define S_IRUSR 0400
#define S_IWUSR 0200
#define S_IXUSR 0100
#define S_IRWXG 0070
#define S_IRWXO 0007''',
        'struct': '''typedef struct { u32 uid; u32 gid; char name[32]; char home[64]; } User;
typedef struct { u32 owner; u32 group; u16 mode; } Permissions;
User user_table[MAX_USERS];''',
        'inline': '''static inline int check_perm(Permissions* p, u32 uid, u32 gid, u8 bits) {
    if (uid == ROOT_UID) return 1;
    if (uid == p->owner) return (p->mode & bits) != 0;
    if (gid == p->group) return (p->mode & (bits>>3)) != 0;
    return (p->mode & (bits>>6)) != 0;
}''',
        'if': '''int fs_check_access(u32 ino, u8 access) {
    u32 uid = sched_current() ? sched_current()->uid : 0;
    u32 gid = sched_current() ? sched_current()->gid : 0;
    if (ino >= MAX_FILES) return 0;
    Permissions* p = &file_perms[ino];
    return check_perm(p, uid, gid, access);
}''',
        'return': '''User* user_find(u32 uid) { if (uid >= MAX_USERS) return NULL; return user_table[uid].name[0] ? &user_table[uid] : NULL; }''',
    },
    'power': {
        'define': '''#define POWER_OFF_PORT 0x604
#define REBOOT_PORT 0x64
#define REBOOT_CMD 0xFE''',
        'inline': '''static inline void outw(u16 port, u16 val) { asm volatile("outw %0, %1"::"a"(val),"Nd"(port)); }''',
        'if': '''void cpu_idle() { if (sched_count() > 0) { asm volatile("hlt"); } }''',
        'return': '''void power_off() { outw(POWER_OFF_PORT, 0x2000); while(1) asm volatile("hlt"); }
void reboot() { u8 g; while((inb(0x64)&2)!=0); outb(REBOOT_PORT, REBOOT_CMD); while(1) asm volatile("hlt"); }''',
    },
    'vfs': {
        'define': '''#define VFS_MAX_MOUNTS 16
#define VFS_MAX_FD 256
#define O_RDONLY 0
#define O_WRONLY 1
#define O_RDWR 2
#define O_CREAT 0100
#define SEEK_SET 0
#define SEEK_CUR 1
#define SEEK_END 2''',
        'struct': '''typedef struct { u32 ino; u32 offset; u32 flags; void* fs_data; } VFSFile;
typedef struct { char name[32]; u32 ino; u32 parent; u32 size; u16 mode; u32 uid; u32 gid; } VFSInode;
VFSFile fd_table[VFS_MAX_FD];
VFSInode inode_table[MAX_FILES];''',
        'inline': '''static inline VFSFile* fd_get(u32 fd) { return (fd < VFS_MAX_FD) ? &fd_table[fd] : NULL; }''',
        'loop': '''u32 vfs_open(const char* name, u32 flags) { u32 ino = 0; for (u32 i = 0; i < MAX_FILES; i++) { int match = 1; for (u32 j = 0; j < 32 && name[j]; j++) { if (inode_table[i].name[j] != name[j]) { match = 0; break; } } if (match && inode_table[i].size > 0) { ino = i; break; } } if (ino == 0) return 0; u32 fd = 0; for (u32 i = 0; i < VFS_MAX_FD; i++) { if (fd_table[i].ino == 0) { fd = i; break; } } fd_table[fd].ino = ino; fd_table[fd].offset = 0; fd_table[fd].flags = flags; return fd; }''',
        'if': '''u32 vfs_read(u32 fd, void* buf, u32 len) { VFSFile* f = fd_get(fd); if (!f || f->ino == 0) return 0; if (f->ino < MAX_FILES) { u32 max_len = inode_table[f->ino].size - f->offset; if (len > max_len) len = max_len; u32 r = fs_read(f->ino, buf, len); f->offset += r; return r; } return 0; }''',
        'return': '''u32 vfs_write(u32 fd, const void* buf, u32 len) { VFSFile* f = fd_get(fd); if (!f || f->ino == 0) return 0; fs_write(f->ino, buf, len); return len; }
void vfs_close(u32 fd) { if (fd < VFS_MAX_FD) { fd_table[fd].ino = 0; fd_table[fd].offset = 0; } }''',
    },
}

os.makedirs('/home/app/natkernel/modules', exist_ok=True)
total = 0

for name, mod in SUBSYSTEMS.items():
    code = f'/* NATKERNEL {name.upper()} — N=6 IR kinds */\n#include "../kernel.h"\n\n'
    for kind in ['define','struct','inline','loop','if','return']:
        if mod.get(kind):
            code += f'/* {kind} */\n{mod[kind]}\n\n'
    
    path = f'/home/app/natkernel/modules/{name}.c'
    with open(path, 'w') as f:
        f.write(code.strip() + '\n')
    lines = len(code.splitlines())
    total += lines
    print(f'{name:12s}: {lines:>4} lines')

print(f'\nTOTAL: {total} lines in {len(SUBSYSTEMS)} modules')
