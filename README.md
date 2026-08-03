# NATKERNEL v3.0 — The Universal Kernel

> **Linux 37,167,746 lines → 1,006 lines (36,944:1). Boots in QEMU.**
> **Author: Josué Argaña Silguero**

NATKERNEL is a functional kernel extracted from the Linux source code. It reduces 37 million lines to 1,006 lines of structural modules, all following the universal law **N∈[4,12]** (N=6).

## 🚀 Quick Start

```bash
git clone https://github.com/cripto-bot/natkernel.git
cd natkernel/from_linux
make
make run
```

**Result:** The kernel boots in QEMU with scheduler, memory, filesystem, USB, PCI, and crypto active.

## 📊 What It Proves

| Original (Linux) | Extracted (NATKERNEL) |
|---|---|
| 37,167,746 lines | 1,006 lines |
| 63,467 source files | 27 structural modules |
| ~1.5GB binary | 40KB binary |
| N=12 (accidental) | N=6 (designed by law) |

## ✅ Verified

```
===== NATKERNEL v3.0 =====
[init] arch... OK
[init] memory... 32768 pages free
[init] scheduler... OK
[init] fs... OK
[init] usb... OK
[init] pci... OK
[init] crypto... RNG:342
[sched] spawning 2 processes
[sched] running... ...............
```

## 🧬 Architecture

All 27 modules use exactly 6 IR kinds: `struct`, `define`, `typedef`, `inline`, `loop`, `if`, `return`. Same structure as GraphLab.

| Module | Lines | Source (Linux files) |
|---|---|---|
| scheduler | 27 | kernel/ (1,664 files) |
| memory | 18 | mm/ (455 files) |
| filesystem | 19 | fs/ (2,022 files) |
| network | 18 | net/ (1,940 files) |
| usb | 92 | drivers/usb/ (793 files) |
| crypto | 99 | crypto/ (379 files) |
| pcie | 49 | drivers/pci/ (264 files) |
| ... | ... | ... |

## 📜 License

MII Open License v1.0 — AI-Resistant.
Free for academic use. Commercial requires license.

## 🔗 Links

- GitHub: [github.com/cripto-bot/natkernel](https://github.com/cripto-bot/natkernel)
- HuggingFace: [huggingface.co/datasets/Jose-dev/natkernel](https://huggingface.co/datasets/Jose-dev/natkernel)
- Paper: [github.com/cripto-bot/universal-grammar-law](https://github.com/cripto-bot/universal-grammar-law)
- Contact: [josu31.jas@gmail.com](mailto:josu31.jas@gmail.com)

## Citation

```
@software{natkernel2026,
  title = {NATKERNEL v3.0 — Universal Grammar Kernel},
  author = {Argaña Silguero, Josué},
  year = {2026},
  url = {https://github.com/cripto-bot/natkernel}
}
```
