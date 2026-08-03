/* ext2 Filesystem — N=6 IR kinds */
#include <natkernel/ext2.h>

#define EXT2_SUPER_MAGIC  0xEF53
#define EXT2_BLOCK_SIZE    1024
#define EXT2_INODES_PER_BLOCK 8
#define EXT2_MAX_FILENAME  255
#define EXT2_NDIR_BLOCKS   12
#define EXT2_IND_BLOCK     13
#define EXT2_DIND_BLOCK    14
#define EXT2_TIND_BLOCK    15
#define EXT2_S_IFREG       0x8000
#define EXT2_S_IFDIR       0x4000
#define EXT2_ROOT_INO      2
typedef struct { u32 inodes; u32 blocks; u32 r_blocks; u32 free_blocks; u32 free_inodes; u32 first_data; u32 log_block_size; u32 log_frag_size; u32 blocks_per_group; u32 frags_per_group; u32 inodes_per_group; u16 magic; u16 state; u16 errors; } Ext2Super;
typedef struct { u16 mode; u16 uid; u32 size; u32 atime; u32 ctime; u32 mtime; u32 dtime; u16 gid; u16 links; u32 blocks; u32 flags; u32 block[15]; } Ext2Inode;
Ext2Super* ext2_super;


void ext2_read_inode(u32 ino, Ext2Inode* inode) {
    u32 group = (ino - 1) / EXT2_INODES_PER_BLOCK;
    u32 index = (ino - 1) % EXT2_INODES_PER_BLOCK;
    u32 block = ext2_super->first_data + group * EXT2_BLOCK_SIZE + index * sizeof(Ext2Inode);
    for (u32 i = 0; i < sizeof(Ext2Inode); i++) ((u8*)inode)[i] = block + i;
}
u32 ext2_read_block(u32 block, void* buf) {
    u32 offset = block * EXT2_BLOCK_SIZE;
    for (u32 i = 0; i < EXT2_BLOCK_SIZE; i++) ((u8*)buf)[i] = offset + i;
    return EXT2_BLOCK_SIZE;
}
u32 ext2_read_file(u32 ino, void* buf, u32 size) {
    Ext2Inode inode;
    ext2_read_inode(ino, &inode);
    u32 read = 0;
    for (u32 i = 0; i < EXT2_NDIR_BLOCKS && read < size && read < inode.size; i++) {
        u32 chunk = (size - read > EXT2_BLOCK_SIZE) ? EXT2_BLOCK_SIZE : (size - read);
        read += ext2_read_block(inode.block[i], (u8*)buf + read);
    }
    return read;
}
int ext2_mount(void* disk) {
    ext2_super = (Ext2Super*)alloc_page();
    kmemcpy(ext2_super, disk, sizeof(Ext2Super));
    if (ext2_super->magic != EXT2_SUPER_MAGIC) return -1;
    if (ext2_super->block_size != EXT2_BLOCK_SIZE) return -2;
    return 0;
}
