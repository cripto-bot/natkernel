/* NATKERNEL Lib — from Linux lib/ (923 files, 428K lines) */
#include "../kernel.h"
typedef struct { u32 id; } lib_data;
#define LIB_VER 1
typedef u32 lib_id;
static inline int lib_ok(void){return 1;}


u32 strlen_k(const char* s) { u32 n=0; while(*s++)n++; return n; }
int strcmp_k(const char* a, const char* b) { while(*a&&*a==*b){a++;b++;} return *a-*b; }
int strncmp_k(const char* a, const char* b, u32 n) { for(u32 i=0;i<n;i++){if(a[i]!=b[i]||!a[i])return a[i]-b[i];} return 0; }
void* memcpy_k(void* d, const void* s, u32 n) { for(u32 i=0;i<n;i++)((u8*)d)[i]=((u8*)s)[i]; return d; }
void* memset_k(void* d, u8 v, u32 n) { for(u32 i=0;i<n;i++)((u8*)d)[i]=v; return d; }
int memcmp_k(const void* a, const void* b, u32 n) { for(u32 i=0;i<n;i++){int d=((u8*)a)[i]-((u8*)b)[i];if(d)return d;} return 0; }
u32 atoi_k(const char* s) { u32 v=0; while(*s>='0'&&*s<='9'){v=v*10+(*s-'0');s++;} return v; }
void* memmove_k(void* d, const void* s, u32 n) { u8 tmp[256]; u32 sz=n>256?256:n; for(u32 i=0;i<sz;i++)tmp[i]=((u8*)s)[i]; for(u32 i=0;i<sz;i++)((u8*)d)[i]=tmp[i]; return d; }
