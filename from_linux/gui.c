/* NATUSER GUI — Framebuffer interface. N=6 ∈ [4,12] */
#include "../kernel.h"

#define GUI_WIDTH  800
#define GUI_HEIGHT 600
#define FB_ADDR    ((u32*)0xE0000000)

/* IR-struct: Window */
typedef struct { u32 x, y, w, h; u32 color; char title[32]; u8 visible; } Window;
static Window wins[8];
static u32 win_count;

/* IR-inline */
void gui_init(void) { for (u32 i = 0; i < GUI_WIDTH * GUI_HEIGHT; i++) FB_ADDR[i] = 0x1a1a2e; }

/* IR-return: Pixel */
void gui_rect(u32 x, u32 y, u32 w, u32 h, u32 color) {
    for (u32 py = y; py < y + h && py < GUI_HEIGHT; py++)
        for (u32 px = x; px < x + w && px < GUI_WIDTH; px++)
            FB_ADDR[py * GUI_WIDTH + px] = color;
}

/* IR-if: Create window */
Window* gui_window(u32 x, u32 y, u32 w, u32 h, const char* title) {
    if (win_count >= 8) return NULL;
    Window* win = &wins[win_count++];
    win->x = x; win->y = y; win->w = w; win->h = h; win->color = 0x16213e; win->visible = 1;
    for (u32 i = 0; title[i] && i < 31; i++) win->title[i] = title[i];
    gui_rect(x, y, w, h, win->color);
    gui_rect(x, y, w, 20, 0x0f3460);
    return win;
}

/* IR-loop: Draw all windows */
void gui_draw(void) {
    for (u32 i = 0; i < win_count; i++) {
        Window* w = &wins[i];
        if (w->visible) { gui_rect(w->x, w->y, w->w, w->h, w->color); gui_rect(w->x, w->y, w->w, 20, 0x0f3460); }
    }
}

/* IR-loop: Desktop */
void gui_desktop(void) {
    gui_window(50, 50, 300, 200, "Terminal");
    gui_window(100, 80, 250, 180, "Files");
    gui_window(400, 50, 350, 150, "System Monitor");
    for (;;) { for (volatile u64 i = 0; i < 50000000; i++) asm volatile("nop"); gui_draw(); }
}
