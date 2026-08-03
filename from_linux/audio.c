/* NATKERNEL Audio — from Linux sound/ (2660 files, 1.6M lines) */
#include "../kernel.h"

#define AUDIO_BUFSZ 4096
#define AUDIO_RATE 44100
#define AUDIO_CHANNELS 2

static i32 audio_buf[AUDIO_BUFSZ];
static u32 audio_wp, audio_rp;
static u32 audio_volume;

void audio_init(void) { audio_wp=0;audio_rp=0;audio_volume=75; for(u32 i=0;i<AUDIO_BUFSZ;i++)audio_buf[i]=0; }

void audio_play(i32* data, u32 len) {
    for(u32 i=0;i<len&&audio_wp<AUDIO_BUFSZ;i++) {
        audio_buf[audio_wp]=(i32)((i32)data[i]*audio_volume/100);
        audio_wp++;
    }
}

u32 audio_record(i32* buf, u32 max) {
    u32 avail=audio_wp>audio_rp?audio_wp-audio_rp:0;
    u32 r=avail>max?max:avail;
    for(u32 i=0;i<r;i++) buf[i]=audio_buf[audio_rp+i];
    audio_rp+=r;
    return r;
}

void audio_mix(i32* buf, u32 len, u32 rate) {
    u32 ratio=AUDIO_RATE/rate;
    for(u32 i=0;i<len;i+=ratio) {
        if(audio_wp<AUDIO_BUFSZ) {
            i32 sum=0; for(u32 j=0;j<ratio&&i+j<len;j++) sum+=buf[i+j];
            audio_buf[audio_wp]=(i32)(sum/ratio);
            audio_wp++;
        }
    }
}

void audio_volume_set(u32 vol) { if(vol<=100)audio_volume=vol; }
u32 audio_volume_get(void) { return audio_volume; }
void audio_silence(u32 samples) { for(u32 i=0;i<samples&&audio_wp<AUDIO_BUFSZ;i++) audio_buf[audio_wp++]=0; }
u32 audio_buffered(void) { return audio_wp-audio_rp; }
