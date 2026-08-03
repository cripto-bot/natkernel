CC = gcc
CFLAGS = -m32 -nostdlib -fno-builtin -fno-stack-protector -nostartfiles -nodefaultlibs -Wall -I..
LD = ld
LDFLAGS = -m elf_i386 -T linker.ld

SRCS = $(wildcard *.c)
OBJS = $(SRCS:.c=.o)
TARGET = natkernel.bin

all: $(TARGET)

$(TARGET): $(OBJS)
	$(LD) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f *.o $(TARGET)

run: $(TARGET)
	qemu-system-x86_64 -kernel $(TARGET) -m 128M -nographic
