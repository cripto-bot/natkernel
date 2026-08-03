/* NATKERNEL CONSOLE — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define CONSOLE_WIDTH 80
#define CONSOLE_HEIGHT 25
#define VGA_ADDR 0xB8000

/* struct */
typedef struct { u32 x,y; u16* buffer; u8 color; } Console;

/* inline */
static inline u16 vga_entry(char c, u8 fg, u8 bg) { return (u16)c | ((u16)(fg | bg<<4) << 8); }
static inline void console_putchar(char c) { u16* vga = (u16*)VGA_ADDR; if (c == '\n') { console.x = 0; console.y++; } else { vga[console.y*CONSOLE_WIDTH+console.x] = vga_entry(c,7,0); if (++console.x >= CONSOLE_WIDTH) { console.x=0; console.y++; } } }

/* loop */
void console_clear() { u16* vga = (u16*)VGA_ADDR; for (u32 i = 0; i < CONSOLE_WIDTH*CONSOLE_HEIGHT; i++) vga[i] = vga_entry(' ', 7, 0); console.x = 0; console.y = 0; }

/* if */
void console_write(const char* s) { while(*s) { if (*s == '\n') { console.x=0; console.y++; s++; } else { console_putchar(*s++); } } ; if (console.y >= CONSOLE_HEIGHT) { for (u32 i=0;i<CONSOLE_WIDTH*(CONSOLE_HEIGHT-1);i++) ((u16*)VGA_ADDR)[i]=((u16*)VGA_ADDR)[i+CONSOLE_WIDTH]; console.y--; } }
