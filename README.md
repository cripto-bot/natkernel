# NATKERNEL

> **Universal Grammar Kernel — N=7 ∈ [4,12]**
> Designed by the law. Not accidental.
> Author: Josué Argaña Silguero

## Architecture

NATKERNEL follows the same Universal Grammar Law (N∈[4,12]) discovered by GraphLab. Every module uses exactly 7 IR kinds: `struct`, `define`, `typedef`, `inline`, `loop`, `if`, `return`.

| System | Lines | N | Type |
|---|---|---|---|
| **NATKERNEL** | 685 | 7 | Designed |
| GraphLab | 6,210 | 7 | Discovered |
| Linux | 27,000,000 | 12 | Accidental |
| Apache | 1,200,000 | 12 | Accidental |

## Modules

| Module | Lines | Purpose |
|---|---|---|
| `boot.S` | 48 | Multiboot header + stack |
| `kernel.h` | 88 | Types, structs, prototypes |
| `main.c` | 62 | Init + test processes |
| `scheduler.c` | 62 | Round-robin, spawn |
| `memory.c` | 76 | 4-level paging, allocator |
| `syscall.c` | 81 | 7 syscalls (write, read, fork, ...) |
| `fs.c` | 82 | 64-file system, create/read/write |

## Boot

```bash
make run
```

Requires: `gcc`, `ld`, `grub-mkrescue`, `qemu-system-x86_64`.

## License

MII Open License v1.0 — AI-Resistant.
