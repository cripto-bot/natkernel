# NATKERNEL v3.0 — Complete Build System
# Linux 37M→1K + BusyBox 274K→NATUSER + 7 new pentest tools
# make all && make run

CC = gcc
LD = ld
CFLAGS = -m32 -nostdlib -fno-builtin -fno-stack-protector -nostartfiles -nodefaultlibs -Wall -I.
LDFLAGS = -m elf_i386 -T linker.ld

KERNEL_OBJS = boot.o syscall_stub.o vfs_stub.o \
    arch.o arm64.o ata.o audio.o block.o crypto.o drivers.o \
    filesystem.o gpu.o headers.o init.o input.o ipc.o lib.o \
    memory.o netdrv.o network.o nvme.o other.o pcie.o riscv.o \
    scheduler.o security.o usb.o virt.o x86.o

USERLAND_OBJS = shell.o
PENTEST_OBJS = pentest.o pentest_adv.o

ALL_OBJS = $(KERNEL_OBJS) $(USERLAND_OBJS) $(PENTEST_OBJS) main.o
TARGET = natkernel.bin

all: $(TARGET)
	@echo ""
	@echo "NATKERNEL v3.0 built: $(TARGET)"
	@ls -lh $(TARGET)
	@echo "Run: make run"

$(TARGET): $(ALL_OBJS)
	$(LD) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.S
	$(CC) -m32 -nostdlib -c $< -o $@

run: $(TARGET)
	@echo "Booting NATKERNEL v3.0..."
	@echo "Commands: scan crack chaos wifi entropy grammar kolmogorov evolve trace ver ls ps echo clear exit"
	@echo ""
	qemu-system-x86_64 -kernel $(TARGET) -m 128M -serial stdio -display none -no-reboot

run-graphic: $(TARGET)
	qemu-system-x86_64 -kernel $(TARGET) -m 128M

clean:
	rm -f *.o $(TARGET)

.PHONY: all run run-graphic clean
