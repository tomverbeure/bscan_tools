#! /usr/bin/env python3

import fileinput
import sys
import getopt

import intel_model

import pprint

pp = pprint.PrettyPrinter(indent=4)


def usage():
    sys.stderr.write("TODO...")
    sys.stderr.write("\n")

try:
    opts, argv = getopt.getopt(sys.argv[1:], "r:", ["rename="])
except getopt.GetoptError as err:
    print(err)
    usage()
    sys.exit(2)

rename_filename = None

for o, a in opts:
    if o in ("-r", "--rename"):
        rename_filename = a

if len(argv) != 1:
    usage()
    sys.exit(2)


TEST_LOGIC_RESET    = 0
RUN_TEST_IDLE       = 1
SELECT_DR_SCAN      = 2
CAPTURE_DR          = 3
SHIFT_DR            = 4
EXIT1_DR            = 5
PAUSE_DR            = 6
EXIT2_DR            = 7
UPDATE_DR           = 8
SELECT_IR_SCAN      = 9
CAPTURE_IR          = 10
SHIFT_IR            = 11
EXIT1_IR            = 12
PAUSE_IR            = 13
EXIT2_IR            = 14
UPDATE_IR           = 15

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def convert_tdi_tdo_str(str):

    # Short format: 0x155
    # Long format:  [0x0FECC0FF020B10DD], [0xFFFFFFFFFFFFFFFF], [0x1]

    val = 0

    str_segments = str.split(",")
    if len(str_segments) == 1:
        val = int(str_segments[0][2:], 16)
    else: 
        val = 0
        start_bit = 0
        for segment in str_segments:
            val += int(segment.strip()[3:-1], 16) << start_bit
            start_bit += 32

    return val

def read_transactions(jtag_filename):
    transactions = []

    state_lookup = {
            "Test-Logic-Reset"  :    TEST_LOGIC_RESET,
            "Run-Test/Idle"     :    RUN_TEST_IDLE,
            "Select-DR-Scan"    :    SELECT_DR_SCAN,
            "Capture-DR"        :    CAPTURE_DR,
            "Shift-DR"          :    SHIFT_DR,
            "Exit1-DR"          :    EXIT1_DR,
            "Pause-DR"          :    PAUSE_DR,
            "Exit2-DR"          :    EXIT2_DR,
            "Update-DR"         :    UPDATE_DR,
            "Select-IR-Scan"    :    SELECT_IR_SCAN,
            "Capture-IR"        :    CAPTURE_IR,
            "Shift-IR"          :    SHIFT_IR,
            "Exit1-IR"          :    EXIT1_IR,
            "Pause-IR"          :    PAUSE_IR,
            "Exit2-IR"          :    EXIT2_IR,
            "Update-IR"         :    UPDATE_IR,
    }

    with open(jtag_filename) as jtag_file:
        first_line = True

        for line in jtag_file:
            if first_line:
                first_line = False
                continue 

            time, tap_state, tdi, tdo, tdi_bits, tdo_bits = line.strip().split(";")

            time = float(time)

            if tap_state in state_lookup:
                tap_state_nr    = state_lookup[tap_state]

            if tdi_bits != "":
                tdi_bits = int(tdi_bits)
            else:
                tdi_bits = 0

            if tdo_bits != "":
                tdo_bits = int(tdo_bits)
            else:
                tdo_bits = 0

            if tdi != "": 
                tdi = convert_tdi_tdo_str(tdi)
            else:
                tdi = None

            if tdo != "": 
                tdo = convert_tdi_tdo_str(tdo)
            else:
                tdo = None

            #print(time, tap_state_nr, tap_state, tdi_bits, tdi, tdo_bits, tdo)

            transaction = {
                    "time"          :       time,
                    "tap_state_nr"  :       tap_state_nr,
                    "tap_state"     :       tap_state,
                    "tdi_bits"      :       tdi_bits,
                    "tdo_bits"      :       tdo_bits,
                    "tdi"           :       tdi,
                    "tdo"           :       tdo,
                    }

            transactions.append(transaction)

    return transactions


transactions = read_transactions(argv[0])

#pp.pprint(transactions)

def match_bit_pattern(pattern, pattern_len, sequence, sequence_len, start_bit):

    for first_bit in range(start_bit, sequence_len-pattern_len):
        pattern_shifted = pattern << first_bit
        sequence_masked = sequence & (((1<<pattern_len)-1) << first_bit)

        if pattern_shifted == sequence_masked:
            return first_bit

    return -1

def reverse_int(value, width):
    b = '{:0{width}b}'.format(value, width=width)
    return int(b[::-1], 2)

special_list = []
for num, transaction in enumerate(transactions):
    if None and transaction["tap_state_nr"] in [SHIFT_DR, SHIFT_IR]:
        bit_nr = match_bit_pattern(ord('e'), 8, transaction["tdi"], transaction["tdi_bits"], 0)
        #bit_nr = match_bit_pattern(0xc0f, 12, transaction["tdi"], transaction["tdi_bits"], 0)
        if bit_nr >= 0:
            print("Transaction nr %d: bit_nr: %d:" % (num, bit_nr))
            pp.pprint(transaction)
            print("0x%x" % transaction["tdi"])
            sys.exit()
        

    if True and transaction["tap_state_nr"] in [SHIFT_DR] and transaction["tdi_bits"] == 643:
        special_list.append(transaction)


diff = 0

for g_num, g in enumerate(chunks(special_list, 8)):
    print("============================================================")
    print("Group %d:" % g_num)

    for n in range(0,8):
        #print("%d: %x" % (n, g[n]["tdi"]))
    
        for nn in range(0, n):
            local_diff = (g[n]["tdi"] ^ g[nn]["tdi"])
            diff = diff | local_diff
            #print("%d, %d: %x: %x, %x" % (n, nn, local_diff, g[n]["tdi"], g[nn]["tdi"]))

    print("   %x, %c" % (diff, chr( (g[0]["tdi"] >> 3) & 0xff)))




