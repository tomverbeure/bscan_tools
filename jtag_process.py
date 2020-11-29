#! /usr/bin/env python3

import fileinput
import sys
import getopt

import scan_chain
from intel_model import *
from jtag import *

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

# There are currenlty no cmd line options...
#rename_filename = None
#
#for o, a in opts:
#    if o in ("-r", "--rename"):
#        rename_filename = a

if len(argv) != 1:
    usage()
    sys.exit(2)


transactions = JtagTransaction.read_saleae_jtag_csv(argv[0])
#pp.pprint(transactions)

# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# Given 2 bit vectors (given as an integer and length in number of bits), pattern
# and sequence, scan the sequence for the first occurence of the pattern, 
# starting at a start bit.
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


# Experimental function to figure out where interesting data might be stored.
def extract_jtag_data(transactions):

    special_list = []
    for num, trans in enumerate(transactions):

        if None and trans.state in [JtagState.SHIFT_DR, JtagState.SHIFT_IR]:
            # Search for a desired value in a JTAG IR or DR transaction

            bit_nr = match_bit_pattern(ord('e'), 8, trans.tdi_value, trans.tdi_length, 0)
            #bit_nr = match_bit_pattern(0xc0f, 12, trans.tdi_value, trans.tdi_length, 0)
            if bit_nr >= 0:
                print("Transaction nr %d: bit_nr: %d:" % (num, bit_nr))
                pp.pprint(trans)
                print("0x%x" % trans.tdi_value)
                sys.exit()
            
        if True and trans.state in [JtagState.SHIFT_DR] and trans.tdi_length == 643:
            # Find all transactions of 632 data bits contain JTAG UART data
            special_list.append(trans)

    diff = 0
    

    print("Special list length: %d" % len(special_list))
    # WTF am I doing here???
    for g_num, g in enumerate(chunks(special_list, 8)):
        print("============================================================")
        print("Group %d (length: %d):" % (g_num, len(g)))

        for n in range(0,8):
            #print("%d: 0x%x" % (n, g[n]["tdi"]))
        
            for nn in range(0, n):
                # Find bit mismatches withint a groupd of 8 JTAG UART transactions. (Why?)
                local_diff = (g[n].tdi_value ^ g[nn].tdi_value)
                diff = diff | local_diff
                #print("%d, %d: 0x%x: 0x%x, 0x%x" % (n, nn, local_diff, g[n]["tdi"], g[nn]["tdi"]))
    
        print("   0x%x, %c" % (diff, chr( (g[0].tdi_value >> 3) & 0xff)))

#extract_jtag_data(transactions)

ep2c5 = IntelEP2C5()

for trans in transactions:
    print("============================================================")
    print(trans)
    if trans.state == JtagState.SHIFT_DR:
        print("Shift-DR: %s\n" % ep2c5.dr_chains[ep2c5.ir_chain.value].name)
    ep2c5.apply_transaction(trans)
    print(ep2c5)
