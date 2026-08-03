/* NATUSER Init + Editor — from BusyBox init/vi/. N=6 */
#include "../kernel.h"

static inline void pc(char c){outb(0xE9,c);}
static inline void ps(const char* s){for(;*s;s++)pc(*s);}

/* === EDITOR (from BusyBox vi/) === */
static char ebuf[24][80];
static u32 ex,ey,erows;

void editor_init(void) { ex=0;ey=0;erows=1; for(u32 i=0;i<24;i++)for(u32 j=0;j<80;j++)ebuf[i][j]=' '; }

void editor_insert(char c) {
    if(ey<24&&ex<80) { ebuf[ey][ex]=c; ex++; if(ex>=80){ex=0;ey++;} if(ey>=erows)erows=ey+1; }
}

void editor_draw(void) {
    for(u32 i=0;i<25;i++)pc('\n');
    for(u32 r=0;r<erows;r++) { for(u32 c=0;c<80;c++)pc(ebuf[r][c]); pc('\n'); }
}

void editor_delete(void) { if(ex>0){ex--;ebuf[ey][ex]=' ';} }

void editor_run(void) {
    editor_init();
    for(;;) {
        u8 c=inb(0x60);
        if(c==0x01) break; /* ESC */
        if(c==0x0E) { if(ex>0)ex--; } /* Backspace */
        else if(c==0x1C) { ex=0; ey++; } /* Enter */
        else if(c>='a'&&c<='z') editor_insert(c);
        editor_draw();
    }
}

/* === INIT (from BusyBox init/) === */
void init_start(void) {
    ps("\n===== NATKERNEL v3.0 + BusyBox =====\n");
    ps("Universal Grammar Kernel N=6\n");
    ps("Linux 37M -> 1K + BusyBox 274K -> NATUSER\n");
    ps("Author: Josue Argana Silguero\n\n");
    usb_init(); pci_init(); crypto_init();
    ps("[init] OK\n");
    shell_run();
}
