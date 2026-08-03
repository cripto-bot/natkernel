/* NATKERNEL Boot — Multiboot header */
.set MAGIC,    0x1BADB002
.set FLAGS,    0x00000007  /* align + mmap + aout */
.set CHECKSUM, -(MAGIC + FLAGS)

.section .multiboot, "a"
.align 8
.long MAGIC
.long FLAGS
.long CHECKSUM

/* AOUT kludge */
.long 0  /* header_addr */
.long 0  /* load_addr */  
.long 0  /* load_end_addr */
.long 0  /* bss_end_addr */
.long 0  /* entry_addr */

/* Graphics mode */
.long 0  /* mode_type */
.long 1024 /* width */
.long 768  /* height */
.long 32   /* depth */

.section .text
.global _start
_start:
    /* Stack setup */
    movl $stack_top, %esp
    movl %esp, %ebp
    
    /* Clear direction flag */
    cld
    
    /* Call kernel */
    call kernel_main
    
    /* Halt if kernel returns */
    cli
    hlt
1:  jmp 1b

/* 16KB stack */
.section .bss, "aw", @nobits
.align 16
stack_bottom:
    .skip 16384
stack_top:
