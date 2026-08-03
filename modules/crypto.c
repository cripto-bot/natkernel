/* NATKERNEL CRYPTO — N=6 IR kinds */
#include "../kernel.h"

/* define */
#define SHA256_OUTPUT 32
#define ED25519_KEY 32

/* inline */
static inline u32 rotr32(u32 x, u32 n) { return (x>>n)|(x<<(32-n)); }
static inline u32 swap32(u32 x) { return ((x>>24)&0xff)|((x<<8)&0xff0000)|((x>>8)&0xff00)|((x<<24)&0xff000000); }

/* loop */
void sha256(const u8* d, u32 len, u8* out) { u32 h[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}; u32 k[64]={0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2}; for (u32 i=0;i<len/64;i++) { const u8* b=d+i*64; u32 w[64]; for (u32 j=0;j<16;j++) w[j]=(b[j*4]<<24)|(b[j*4+1]<<16)|(b[j*4+2]<<8)|b[j*4+3]; for (u32 j=16;j<64;j++) { u32 s0=rotr32(w[j-15],7)^rotr32(w[j-15],18)^(w[j-15]>>3); u32 s1=rotr32(w[j-2],17)^rotr32(w[j-2],19)^(w[j-2]>>10); w[j]=w[j-16]+s0+w[j-7]+s1; } u32 a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],h2=h[7]; for (u32 j=0;j<64;j++) { u32 S1=rotr32(e,6)^rotr32(e,11)^rotr32(e,25); u32 ch=(e&f)^((~e)&g); u32 t1=h2+S1+ch+k[j]+w[j]; u32 S0=rotr32(a,2)^rotr32(a,13)^rotr32(a,22); u32 maj=(a&b)^(a&c)^(b&c); u32 t2=S0+maj; h2=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2; } h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=h2; } for (u32 j=0;j<8;j++) { out[j*4]=h[j]>>24;out[j*4+1]=(h[j]>>16)&0xFF;out[j*4+2]=(h[j]>>8)&0xFF;out[j*4+3]=h[j]&0xFF; } }

/* if */
u32 random_u32() { static u64 seed = 123456789; seed = seed * 6364136223846793005ULL + 1442695040888963407ULL; return (u32)(seed >> 32); }

/* return */
void random_bytes(u8* buf, u32 len) { for (u32 i = 0; i < len; i += 4) { u32 r = random_u32(); for (u32 j = 0; j < 4 && i+j < len; j++) buf[i+j] = (u8)(r >> (j*8)); } }
