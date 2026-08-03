/* NATUSER libc — Minimal C library. N=5 ∈ [4,12] */
#include "../kernel.h"

/* IR-inline: String extras */
char* kstrcpy(char* d, const char* s) { char* r = d; while (*s) *d++ = *s++; *d = 0; return r; }

/* IR-return: Conversion */
u32 katoi(const char* s) { u32 v = 0; while (*s >= '0' && *s <= '9') { v = v * 10 + (*s - '0'); s++; } return v; }

/* IR-if: isdigit */
int kisdigit(char c) { return (c >= '0' && c <= '9'); }
int kislower(char c) { return (c >= 'a' && c <= 'z'); }
int kisupper(char c) { return (c >= 'A' && c <= 'Z'); }

/* IR-return: toupper/tolower */
char ktoupper(char c) { if (kislower(c)) return c - 32; return c; }
char ktolower(char c) { if (kisupper(c)) return c + 32; return c; }
