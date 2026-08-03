/* NATKERNEL Headers — from Linux include/ (10,258 files, 1.9M lines) */
#include "../kernel.h"

#define likely(x)   __builtin_expect(!!(x), 1)
#define unlikely(x) __builtin_expect(!!(x), 0)
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define container_of(ptr, type, member) ((type*)((u8*)(ptr)-((u64)&((type*)0)->member)))
#define ALIGN(x, a) (((x)+(a)-1)&~((a)-1))
#define MIN(a, b) ((a)<(b)?(a):(b))
#define MAX(a, b) ((a)>(b)?(a):(b))
#define BIT(n) (1ULL<<(n))
#define GENMASK(h, l) (((1ULL<<((h)-(l)+1))-1)<<(l))
#define IS_ALIGNED(x, a) (((x)&((a)-1))==0)
#define round_up(x, y) (((x)+(y)-1)&~((y)-1))
#define DIV_ROUND_UP(n, d) (((n)+(d)-1)/(d))
#define swap(a, b) do { typeof(a) _t=a; a=b; b=_t; } while(0)

static inline u32 ilog2(u32 n) { u32 r=0; while(n>>=1)r++; return r; }
static inline int is_power_of_2(u64 n) { return n&&!(n&(n-1)); }
