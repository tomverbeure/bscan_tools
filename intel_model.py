
import collections

from scan_chain import *
from jtag import *

class Chip:

    def __init__(self, name, ir_length, ir_reset_value, idcode, idcode_ir):

        self.ir_chain   = FixedLengthScanChain("IR", ir_length, ir_reset_value)
        self.dr_chains  = {}

        idcode_chain    = IdCodeScanChain(idcode)
        bypass_chain    = BypassScanChain()

        self.dr_chains  = collections.OrderedDict()

        self.dr_chains[idcode_ir]        = idcode_chain
        self.dr_chains[(1<<ir_length)-1] = bypass_chain

        pass

    def apply_transaction(self, transaction):

        if transaction["tap_state_nr"] == JtagState.TEST_LOGIC_RESET:
            self.ir_chain.reset()
            for dr in self.dr_chains.values():
                dr.reset()

        elif transaction["tap_state_nr"] == JtagState.SHIFT_IR:
            self.ir_chain.shift(transaction)

        elif transaction["tap_state_nr"] == JtagState.SHIFT_DR:
            if self.ir_chain.value in self.dr_chains:
                cur_dr = self.dr_chains[self.ir_chain.value]
                cur_dr.shift(transaction)

            else:
                print("Unknown DR chain: %x" % self.ir_chain.value)

            pass

        pass


    def __str__(self):

        s = ""
        s += self.ir_chain.__str__()
        s += "\n"

        for ir_code, dr in self.dr_chains.items():
            s += "IR code: %x\n" % ir_code
            s += dr.__str__()
            s += "\n"

        return s

class IntelFpga(Chip):

    MANUFACTURER_ID = "00001101110"

    IR_CODES = {
        "SAMPLE_PRELOAD"     : int("0000000101", 2),
        "EXTEST"             : int("0000001111", 2),
        "BYPASS"             : int("1111111111", 2),
        "USERCODE"           : int("0000000111", 2),
        "IDCODE"             : int("0000000110", 2),
        "HIGHZ"              : int("0000001011", 2),
        "CLAMP"              : int("0000001010", 2),
        "PULSE_NCONFIG"      : int("0000000001", 2),
        "CONFIG_IO"          : int("0000001101", 2),
    }

    def __init__(self, name, idcode):

        super().__init__(name, 10, IntelFpga.IR_CODES["IDCODE"], idcode, IntelFpga.IR_CODES["IDCODE"])
        pass

class IntelEP2C5(IntelFpga):

    def __init__(self):

        idcode  = int(''.join(("0000", "0010000010110001", IntelFpga.MANUFACTURER_ID, "1")), 2)
        super().__init__("EP2C5", idcode)
        pass

