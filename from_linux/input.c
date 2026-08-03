/* NATKERNEL Input — from Linux drivers/input/ (455 files, 217K lines) */
#include "../kernel.h"

#define MAX_EVENTS 256
#define KEY_ESC 1
#define KEY_ENTER 28
#define KEY_SHIFT 42
#define KEY_CTRL 29
#define KEY_ALT 56
#define KEY_UP 72
#define KEY_DOWN 80
#define KEY_LEFT 75
#define KEY_RIGHT 77

typedef struct { u8 type, code; u32 value; } InputEvent;
static InputEvent ev_buf[MAX_EVENTS];
static u32 ev_head, ev_tail;
static u8 key_state[128];
static u32 mouse_x, mouse_y;
static u8 mouse_btn;

void input_init(void) { ev_head=0;ev_tail=0;mouse_x=512;mouse_y=384; for(u32 i=0;i<128;i++)key_state[i]=0; }

void input_push(u8 type, u8 code, u32 value) {
    ev_buf[ev_tail].type=type; ev_buf[ev_tail].code=code; ev_buf[ev_tail].value=value;
    ev_tail=(ev_tail+1)%MAX_EVENTS;
    if(ev_tail==ev_head) ev_head=(ev_head+1)%MAX_EVENTS;
}

int input_pop(InputEvent* ev) {
    if(ev_head==ev_tail) return 0;
    *ev=ev_buf[ev_head]; ev_head=(ev_head+1)%MAX_EVENTS; return 1;
}

void kb_handler(u8 sc) {
    u8 pressed=!(sc&0x80); u8 key=sc&0x7F;
    key_state[key]=pressed;
    input_push(1, key, pressed);
}

void mouse_handler(u8 dx, u8 dy, u8 btn) {
    mouse_x=(u32)((i32)mouse_x+dx); if(mouse_x>1023)mouse_x=1023;
    mouse_y=(u32)((i32)mouse_y-dy); if(mouse_y>767)mouse_y=767;
    mouse_btn=btn;
}

u8 input_keydown(u8 key) { return key<128?key_state[key]:0; }
u32 input_mouse_x(void) { return mouse_x; }
u32 input_mouse_y(void) { return mouse_y; }
u8 input_mouse_btn(void) { return mouse_btn; }
