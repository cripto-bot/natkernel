# NATKERNEL Makefile — Universal Grammar Kernel
# N=7 IR kinds. Designed, not accidental.

CC = gcc
AS = as
LD = ld
CFLAGS = -m32 -nostdlib -nostdinc -fno-builtin -fno-stack-protector \
         -nostartfiles -nodefaultlibs -Wall -Wextra -c \
         -mno-mmx -mno-sse -mno-sse2
LDFLAGS = -T linker.ld -m elf_i386
ASFLAGS = --32

OBJS = boot.o main.o scheduler.o memory.o syscall.o fs.o
TARGET = natkernel.bin
ISO = natkernel.iso

all: $(ISO)

$(TARGET): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $^

%.o: %.c kernel.h
	$(CC) $(CFLAGS) $< -o $@

%.o: %.S
	$(AS) $(ASFLAGS) $< -o $@

$(ISO): $(TARGET)
	mkdir -p iso/boot/grub
	cp $(TARGET) iso/boot/
	cp grub.cfg iso/boot/grub/
	grub-mkrescue -o $(ISO) iso/ 2>/dev/null || echo "Install grub-mkrescue for ISO"

run: $(ISO)
	qemu-system-x86_64 -cdrom $(ISO) -m 128M

clean:
	rm -rf *.o $(TARGET) $(ISO) iso/

lines:
	@echo "NATKERNEL — $(shell wc -l *.c *.h *.S | tail -1) lines"
	@echo "Modules: scheduler memory syscall fs main boot"
