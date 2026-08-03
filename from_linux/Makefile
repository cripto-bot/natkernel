CC = gcc
AS = as
LD = ld
CFLAGS = -m32 -nostdlib -fno-builtin -fno-stack-protector -nostartfiles -nodefaultlibs -Wall -I..
ASFLAGS = --32
LDFLAGS = -m elf_i386 -T linker.ld

OBJS = boot.o syscall_stub.o arch.o arm64.o ata.o audio.o block.o crypto.o drivers.o \
       filesystem.o gpu.o headers.o init.o input.o ipc.o lib.o main.o memory.o \
       netdrv.o network.o nvme.o other.o pcie.o riscv.o scheduler.o security.o \
       usb.o virt.o x86.o
TARGET = natkernel.bin

all: $(TARGET)
	@echo "NATKERNEL v3.0 built: $(TARGET)"
	@ls -lh $(TARGET)

$(TARGET): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

%.o: %.S
	$(CC) -m32 -nostdlib -c $< -o $@

run: $(TARGET)
	qemu-system-x86_64 -kernel $(TARGET) -m 128M -debugcon stdio -display none -no-reboot

clean:
	rm -f *.o $(TARGET)
