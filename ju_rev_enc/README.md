
jtaguart: 110:128 v1
signaltap: 110:0 v6
signals and probes: 110:9 v0

# HUB

156: Shift-DR - TDI 0 - TDO 5 - 7
161: Shift-DR - TDI 0 - TDO 0 - 7
166: Shift-DR - TDI 0 - TDO e - 7
171: Shift-DR - TDI 0 - TDO 6 - 7
176: Shift-DR - TDI 0 - TDO 0 - 7
181: Shift-DR - TDI 0 - TDO 1 - 7
186: Shift-DR - TDI 0 - TDO 8 - 7
191: Shift-DR - TDI 0 - TDO 0 - 7

0810 -> 0000_1 000_0001_0 000
          v1       1       0?

# JTAG_UART

110:128 v1

196: Shift-DR - TDI 0 - TDO 0 - 7
201: Shift-DR - TDI 0 - TDO 0 - 7
206: Shift-DR - TDI 0 - TDO e - 7
211: Shift-DR - TDI 0 - TDO 6 - 7
216: Shift-DR - TDI 0 - TDO 0 - 7
221: Shift-DR - TDI 0 - TDO 0 - 7
226: Shift-DR - TDI 0 - TDO c - 7
231: Shift-DR - TDI 0 - TDO 0 - 7

110 0x6e
128 0b10000000

0c00 -> 0000_1 100_0000_0 000
          v1     128       0?

# Signals & Probes

signals and probes: 110:9 v0

236: Shift-DR - TDI 0 - TDO 0 - 7
241: Shift-DR - TDI 0 - TDO 0 - 7
246: Shift-DR - TDI 0 - TDO e - 7
251: Shift-DR - TDI 0 - TDO 6 - 7
256: Shift-DR - TDI 0 - TDO 8 - 7
261: Shift-DR - TDI 0 - TDO 4 - 7
266: Shift-DR - TDI 0 - TDO 0 - 7
271: Shift-DR - TDI 0 - TDO 0 - 7

Signal & Probe -> 110:9 v0

110 0x6e
9   0b00001001

0048 -> 0000_0 000_0100_1 000
          v0       9       0?

# Signal Tap

signaltap: 110:0 v6

144: Shift-DR - TDI 0 - TDO 0 - 7
149: Shift-DR - TDI 0 - TDO 0 - 7
154: Shift-DR - TDI 0 - TDO e - 7
159: Shift-DR - TDI 0 - TDO 6 - 7
164: Shift-DR - TDI 0 - TDO 0 - 7
169: Shift-DR - TDI 0 - TDO 0 - 7
174: Shift-DR - TDI 0 - TDO 0 - 7
179: Shift-DR - TDI 0 - TDO 3 - 7

110     0x63
0       0b00000000
6       0b0110

3000 -> 0011_0 000_0000_0 000
          v6        0      0?


After SLD enumeration:



# System Console commands:


## Send bytes to jtag_uart

https://www.intel.co.jp/content/dam/altera-www/global/ja_JP/pdfs/literature/ug/ug_system_console.pdf -> Bytestream Service

```
set bytestream_index 0
set bytestream [lindex [get_service_paths bytestream] $bytestream_index]
set claimed_bytestream [claim_service bytestream $bytestream mylib]
set payload [list 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99]
bytestream_send $claimed_bytestream $payload
```

