/* NATKERNEL NVMe — from Linux drivers/nvme/ (98 files, 70K lines) */
#include "../kernel.h"

#define NVME_QSIZE 64
#define NVME_CREATE_IO_SQ 1
#define NVME_DELETE_IO_SQ 0
#define NVME_IO_WRITE 1
#define NVME_IO_READ 2

typedef struct { u64 cmd_id; u32 nsid; u64 prp1,prp2; u32 cdw[6]; } NVMeCmd;
typedef struct { u64* sq; u64* cq; u16 sq_h,sq_t,cq_h; u32 phase; u8 id; } NVMeQ;

static NVMeQ admin_q, io_q;
static NVMeCmd* cmds[256];

void nvme_init(void) {
    admin_q.sq=(u64*)alloc_page(); admin_q.cq=(u64*)alloc_page();
    io_q.sq=(u64*)alloc_page(); io_q.cq=(u64*)alloc_page();
    for(u32 i=0;i<NVME_QSIZE;i++){admin_q.sq[i]=0;admin_q.cq[i]=0;io_q.sq[i]=0;io_q.cq[i]=0;}
}

int nvme_submit_admin(NVMeCmd* cmd) {
    admin_q.sq[admin_q.sq_t]=*(u64*)cmd;
    admin_q.sq_t=(admin_q.sq_t+1)&(NVME_QSIZE-1);
    return admin_q.sq_t-1;
}
int nvme_submit_io(NVMeCmd* cmd) {
    io_q.sq[io_q.sq_t]=*(u64*)cmd;
    io_q.sq_t=(io_q.sq_t+1)&(NVME_QSIZE-1);
    return io_q.sq_t-1;
}
int nvme_complete_admin(u64* res) { if(admin_q.cq_h==admin_q.sq_t)return 0;*res=admin_q.cq[admin_q.cq_h];admin_q.cq_h=(admin_q.cq_h+1)&(NVME_QSIZE-1);return 1; }
int nvme_complete_io(u64* res) { if(io_q.cq_h==io_q.sq_t)return 0;*res=io_q.cq[io_q.cq_h];io_q.cq_h=(io_q.cq_h+1)&(NVME_QSIZE-1);return 1; }

int nvme_read(u32 nsid, u64 lba, void* buf, u32 cnt) {
    NVMeCmd cmd = {0}; cmd.nsid=nsid; cmd.cdw[0]=NVME_IO_READ; cmd.prp1=(u64)buf;
    return nvme_submit_io(&cmd);
}
int nvme_write(u32 nsid, u64 lba, const void* buf, u32 cnt) {
    NVMeCmd cmd = {0}; cmd.nsid=nsid; cmd.cdw[0]=NVME_IO_WRITE; cmd.prp1=(u64)buf;
    return nvme_submit_io(&cmd);
}
