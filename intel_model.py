
import collections

from scan_chain import *
from jtag import *

class Chip:

    def __init__(self, name, ir_length, ir_reset_value, ir_capture_value, idcode, idcode_ir):

        self.ir_chain   = IrScanChain(ir_length, ir_reset_value, ir_capture_value)
        self.dr_chains  = {}

        idcode_chain    = IdCodeScanChain(idcode)
        bypass_chain    = BypassScanChain()

        self.dr_chains  = collections.OrderedDict()

        self.dr_chains[idcode_ir]        = idcode_chain
        self.dr_chains[(1<<ir_length)-1] = bypass_chain

        pass

    def apply_transaction(self, transaction):

        if transaction.state == JtagState.TEST_LOGIC_RESET:
            self.ir_chain.reset()
            for dr in self.dr_chains.values():
                dr.reset()

        elif transaction.state == JtagState.SHIFT_IR:
            self.ir_chain.shift(transaction)

        elif transaction.state == JtagState.SHIFT_DR:
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

class SLDNode:

    def __init__(self):

        pass

    pass

class SLDModel:

    def __init__(self, vdr_chain, vir_chain):

        self.vdr_chain = vdr_chain
        self.vir_chain = vir_chain

        self.enumeration_idx = 0
        self.enumeration_array = []

        self.sld_nodes = []

        pass

    def update_vir(self):

        if self.vir_chain.value == 0:
            self.enumeration_idx = 0

        pass

    def shift_dr(self, trans):

        if self.vir_chain.value == 0:

            if trans.tdo_length != 7:
                print("Error: unexpected SLD enumeration chain length: %d (act) != %d (exp)" % (trans.tdo_length, 7))

            if trans.tdi_value != 0:
                print("Error: unexpected TDI value during SLD enumeration: %x" % trans.tdi_value)

            if trans.tdo_value > 15:
                print("Error: TDO value larger than 15 during SLD enumeration: %x" % trans.tdo_value)

            if len(self.enumeration_array) <= self.enumeration_idx:
                # Fill in the value that was sent out
                self.enumeration_array.append(trans.tdo_value)
                self.enumeration_idx += 1

                print("Note: adding %x to enumeration array." % trans.tdo_value)

                if (self.enumeration_idx % 8) == 0:
                    enum_id = 0
                    for i in range(0,8):
                        enum_id += (self.enumeration_array[self.enumeration_idx-8+i] & 0xf) << (i * 4)

                    if self.enumeration_idx == 8:
                        self.m_bits         =  enum_id        & 0xff
                        self.hub_mfg_id     = (enum_id >> 8)  & 0xff
                        self.hub_num_nodes  = (enum_id >> 19) & 0xff
                        self.hub_rev        = (enum_id >> 27) & 0x1f

                        print("Note: new SLD hub : %08x: mfg id: %d, nr nodes: %d, hub rev: %d, m: %d" % (enum_id, self.hub_mfg_id, self.hub_num_nodes, self.hub_rev, self.m_bits))

                    else:
                        sld_node = SLDNode()

                        sld_node.inst_id    =  enum_id        & 0xff
                        sld_node.mfg_id     = (enum_id >> 8)  & 0xff
                        sld_node.node_id    = (enum_id >> 19) & 0xff
                        sld_node.rev        = (enum_id >> 27) & 0x1f

                        self.sld_nodes.append(sld_node)

                        print("Note: new SLD item: %08x: mfg id: %d, node id: %d, node rev: %d, inst id: %d" % (enum_id, sld_node.mfg_id, sld_node.node_id, sld_node.rev, sld_node.inst_id))


        pass

    def n_bits(self):

        return self.hub_num_ndes

    def __str__():
        
        s = ""

        return s



class User0ScanChain(ScanChain):

    def __init__(self):

        super().__init__("USER0 - VDR")

        self.sld_model = None

        # There will be many different lengths, depending on which VDR is selected.

        pass

    def shift(self, trans):

        self.sld_model.shift_dr(trans)

        pass


class User1ScanChain(FixedLengthScanChain):

    def __init__(self):

        super().__init__(name = "USER1 - VIR", length = None, reset_value = 0, read_only = False)
        self.sld_model = None

        pass

    def shift(self, trans):

        if self.length is None:
            for i in range(0,trans.tdi_length):
                tdo_shift = trans.tdo_value >> i
                tdi_masked = trans.tdi_value & ((1<<(trans.tdi_length-i))-1)
                if tdo_shift == tdi_masked:
                    self.length = i
                    print("Note: USER1 chain length: %d" % self.length)
                    break

            if self.length is None:

                if trans.tdo_value == ((1<<trans.tdo_length)-1):
                    print("Note: no USER1 chain present.\n")
                else:
                    print("Error: couldn't figure out USER1 chain length!\n")


        super().shift(trans)

        self.sld_model.update_vir()
        pass

    def __str__(self):

        s = super().__str__()
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
        "USER0"              : int("0000001100", 2),
        "USER1"              : int("0000001110", 2),
    }

    def __init__(self, name, idcode):

        super().__init__(name, 10, IntelFpga.IR_CODES["IDCODE"], 0x155, idcode, IntelFpga.IR_CODES["IDCODE"])

        user0 = User0ScanChain()
        user1 = User1ScanChain()

        self.sld_model = SLDModel(user0, user1)
        user0.sld_model = self.sld_model
        user1.sld_model = self.sld_model

        self.dr_chains[ IntelFpga.IR_CODES["USER0"] ] = user0
        self.dr_chains[ IntelFpga.IR_CODES["USER1"] ] = user1

        pass

class IntelEP2C5(IntelFpga):

    def __init__(self):

        idcode  = int(''.join(("0000", "0010000010110001", IntelFpga.MANUFACTURER_ID, "1")), 2)
        super().__init__("EP2C5", idcode)
        pass

