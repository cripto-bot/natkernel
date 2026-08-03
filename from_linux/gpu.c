/* NATKERNEL GPU — from Linux drivers/gpu/ (7561 files, 8.2M lines) */
#include "../kernel.h"

#define FB_W 1024
#define FB_H 768
#define FB_ADDR 0xE0000000

static u32* fb;
static u32 gpu_color;

void gpu_init(void) {
    fb = (u32*)FB_ADDR;
    gpu_color = 0x000000;
    for(u32 i=0;i<FB_W*FB_H;i++) fb[i]=0x000000;
}

void gpu_fill(u32 color) { gpu_color=color; for(u32 i=0;i<FB_W*FB_H;i++) fb[i]=color; }
void gpu_pixel(u32 x, u32 y, u32 color) { if(x<FB_W&&y<FB_H) fb[y*FB_W+x]=color; }
void gpu_rect(u32 x, u32 y, u32 w, u32 h, u32 color) { for(u32 py=y;py<y+h&&py<FB_H;py++) for(u32 px=x;px<x+w&&px<FB_W;px++) fb[py*FB_W+px]=color; }
void gpu_char(u32 x, u32 y, char c, u32 fg, u32 bg) {
    for(u32 py=0;py<16;py++) for(u32 px=0;px<8;px++) gpu_pixel(x+px,y+py,(c&(1<<px))?fg:bg);
}
void gpu_text(u32 x, u32 y, const char* s, u32 fg, u32 bg) { for(u32 i=0;s[i];i++) gpu_char(x+i*8,y,s[i],fg,bg); }
void gpu_line(u32 x1, u32 y1, u32 x2, u32 y2, u32 color) {
    i32 dx=x2-x1,dy=y2-y1,steps=dx>dy?dx:dy; if(steps<0)steps=-steps; if(steps==0)return;
    for(i32 i=0;i<=steps;i++) gpu_pixel(x1+dx*i/steps,y1+dy*i/steps,color);
}
u32* gpu_fb(void) { return fb; }
