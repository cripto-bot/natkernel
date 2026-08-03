/* NATKERNEL ATA — from Linux drivers/ata/ (138 files, 94K lines) */
#include "../kernel.h"

#define ATA_DATA 0x1F0
#define ATA_ERR  0x1F1
#define ATA_FEAT 0x1F1
#define ATA_SEC  0x1F2
#define ATA_LBAL 0x1F3
#define ATA_LBAM 0x1F4
#define ATA_LBAH 0x1F5
#define ATA_DRIVE 0x1F6
#define ATA_CMD  0x1F7
#define ATA_STAT 0x1F7
#define ATA_READ 0x20
#define ATA_WRITE 0x30
#define ATA_IDENTIFY 0xEC

static u8 ata_present;

void ata_init(void) {
    outb(ATA_DRIVE, 0xA0);
    outb(ATA_CMD, ATA_IDENTIFY);
    if(inb(ATA_STAT)==0) { ata_present=0; return; }
    while(inb(ATA_STAT)&0x80);
    while(!(inb(ATA_STAT)&0x08));
    ata_present=1;
}

static int ata_wait(void) {
    for(u32 i=0;i<100000;i++) {
        u8 s=inb(ATA_STAT);
        if(!(s&0x80)&&(s&0x08)) return 1;
    }
    return 0;
}

int ata_read(u32 lba, void* buf, u16 cnt) {
    if(!ata_present) return 0;
    outb(ATA_DRIVE, 0xE0|((lba>>24)&0x0F));
    outb(ATA_FEAT, 0); outb(ATA_SEC, cnt&0xFF); outb(ATA_LBAL, lba&0xFF);
    outb(ATA_LBAM, (lba>>8)&0xFF); outb(ATA_LBAH, (lba>>16)&0xFF);
    outb(ATA_CMD, ATA_READ);
    if(!ata_wait()) return 0;
    for(u32 i=0;i<cnt*256;i++) ((u16*)buf)[i]=inw(ATA_DATA);
    return cnt;
}

int ata_write(u32 lba, const void* buf, u16 cnt) {
    if(!ata_present) return 0;
    outb(ATA_DRIVE, 0xE0|((lba>>24)&0x0F));
    outb(ATA_SEC, cnt&0xFF); outb(ATA_LBAL, lba&0xFF);
    outb(ATA_LBAM, (lba>>8)&0xFF); outb(ATA_LBAH, (lba>>16)&0xFF);
    outb(ATA_CMD, ATA_WRITE);
    if(!ata_wait()) return 0;
    for(u32 i=0;i<cnt*256;i++) outw(ATA_DATA, ((u16*)buf)[i]);
    return cnt;
}

int ata_present_dev(void) { return ata_present; }
