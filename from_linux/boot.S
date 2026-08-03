/* NATKERNEL Boot — Multiboot header embedded in .text */
.set MAGIC,    0x1BADB002
.set FLAGS,    0x00000003
.set CHECKSUM, -(MAGIC + FLAGS)

.section .text
.align 8
.global _start
.global multiboot_header
multiboot_header:
    .long MAGIC
    .long FLAGS
    .long CHECKSUM

_start:
    movl $stack_top, %esp
    movl %esp, %ebp
    cld
    call kernel_main
    cli
    hlt
1:  jmp 1b

.section .bss, "aw", @nobits
.align 16
stack_bottom:
    .skip 16384
stack_top:
