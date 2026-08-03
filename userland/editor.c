/* NATUSER Editor — Text editor. N=5 ∈ [4,12] */
#include "../kernel.h"

#define EDIT_ROWS 24
#define EDIT_COLS 80
static char edit_buf[EDIT_ROWS][EDIT_COLS + 1];
static u32 cursor_x, cursor_y;
static u32 edit_rows;

/* IR-inline */
static inline void putc_e(char c) { outb(0xE9, c); }

/* IR-loop: Initialize */
void editor_init(void) {
    cursor_x = 0; cursor_y = 0; edit_rows = 1;
    for (u32 i = 0; i < EDIT_ROWS; i++) for (u32 j = 0; j < EDIT_COLS; j++) edit_buf[i][j] = ' ';
}

/* IR-loop: Draw editor */
void editor_draw(void) {
    for (u32 i = 0; i < 25; i++) putc_e('\n');
    putc_e('='); for (u32 i = 0; i < 78; i++) putc_e('=');
    putc_e('\n');
    for (u32 r = 0; r < edit_rows; r++) {
        for (u32 c = 0; c < EDIT_COLS; c++) putc_e(edit_buf[r][c]);
        putc_e('\n');
    }
    for (u32 i = 0; i < 60; i++) putc_e('=');
}

/* IR-if: Insert character */
void editor_insert(char c) {
    if (cursor_y >= EDIT_ROWS || cursor_x >= EDIT_COLS) return;
    if (edit_rows < EDIT_ROWS && cursor_y == edit_rows - 1) edit_rows++;
    edit_buf[cursor_y][cursor_x] = c;
    cursor_x++;
    if (cursor_x >= EDIT_COLS) { cursor_x = 0; cursor_y++; }
}

/* IR-return: Delete */
void editor_delete(void) {
    if (cursor_x > 0) { cursor_x--; edit_buf[cursor_y][cursor_x] = ' '; }
}
