
import collections
import math

from scan_chain import *
from jtag import *

class Chip:

    def __init__(self, name, ir_length, ir_reset_value, ir_capture_value, idcode, idcode_ir):

        # All chips have an IR chain
        self.ir_chain   = IrScanChain(ir_length, ir_reset_value, ir_capture_value)

        # DR chains are chip specific, but we assume there are at least 2 default ones in 
        # all chips: IDCODE and BYPASS 
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
                print("Unknown DR chain: 0x%x" % self.ir_chain.value)

            pass

        pass


    def __str__(self, indent = 0):
        # Dump the status of all scan chains
        indent_str = ' ' * (indent * 4)

        s = "IR chain:\n"
        s += self.ir_chain.__str__(indent+1)
        s += "\n"

        for ir_code, dr in self.dr_chains.items():
            s += "DR chain (IR code: 0x%x):" % ir_code
            if ir_code == self.ir_chain.value:
                s += "       <<<<< SELECTED"
            s += "\n"

            s += dr.__str__(indent+1)
            s += "\n"

        return s


# Generic System Level Debugging node.
# Each SLD node has its own IR and, optionally, a bunch of DR
# https://www.intel.com/content/dam/www/programmable/us/en/pdfs/literature/ug/ug_virtualjtag.pdf
class SLDNode:

    KNOWN_SLDs = { }

    def __init__(self):

        self.mfg_id         = None
        self.node_id        = None
        self.rev            = None
        self.inst_id        = None

        self.sld_model      = None

        # The vir_chain of an SLDNode is not identical to the vir_chain of the SLDModel: 
        # values get shifted into the vir_chain of the SLDModel, and the lower bits get
        # get present to the SLDNode.
        self.vir_chain      = IrScanChain(length = None, reset_value = None, capture_value = None)
        
        self.vdr_chains     = collections.OrderedDict()

        pass

    def name(self):
        return "<Unknown SLD Node>"

    def update_vir(self, value):
        masked_value = value & ((1<<self.vir_chain.length)-1)

        if masked_value != value:
            print("Error: VIR assigned value (0x%x) exceeds VIR chain length (%d)!" % (value, self.vir_chain.length))
            print(self)

        self.vir_chain.value = masked_value
        pass

    def shift_vdr(self, trans):
        print("Error: Unimplemented VDR shift! (VIR value: 0x%x)" % (self.vir_chain.value))
        pass

    def factory(mfg_id, node_id, rev, inst_id, sld_model):
        id = mfg_id * 256 + node_id

        if id in SLDNode.KNOWN_SLDs:
            node = SLDNode.KNOWN_SLDs[id]()
        else:
            node = SLDNode()

        node.mfg_id     = mfg_id
        node.node_id    = node_id
        node.rev        = rev
        node.inst_id    = inst_id

        node.sld_model  = sld_model
        return node

    def inst_id_str(self):

        if self.inst_id is not None:
            return str(self.inst_id)
        else:
            return "None"

    def __str__(self, indent = 0):

        indent_str = ' ' * (indent * 4)

        s = ""
        s += indent_str + "mfg id: %d, node id: %d, rev id: %d, inst id: %s" % (self.mfg_id, self.node_id, self.rev, self.inst_id_str())
        key = self.mfg_id * 256 + self.node_id
        if key in SLDNode.KNOWN_SLDs:
            s += " (%s)" % self.name()
        else:
            s += " (<Unknown>)"
        s+= "\n"

        s += self.vir_chain.__str__(indent+1)

        for vdr_code, vdr in self.vdr_chains.items():
            s += "\n"
            s += indent_str + "    VDR code:  0x%x\n" % vdr_code
            s += vdr.__str__(indent+1)
            s += "\n"

        return s

    pass

class SLDHub(SLDNode):

    def __init__(self):
        super().__init__()

        self.vir_chain.length = 4

        # During enumeration, there are 8 7-bit values shifted out from the DR register.
        # We record them as we go and store them in enumeration_array.
        # When we reach the 8th value, we can decode these 8 values and determine what kind of SLD node
        # has been discovered.
        self.enumeration_idx = 0
        self.enumeration_array = []

    def name(self):
        return "SLD Hub"

    def update_vir(self, value):
        super().update_vir(value)

        if value == 0:
            self.enumeration_idx = 0

    def shift_vdr(self, trans):

        if self.vir_chain.value == 0:
            # When VIR is set to 0, the host can scan out the enumeration values.

            if trans.tdo_length != 7:
                print("Error: unexpected SLD enumeration chain length: %d (act) != %d (exp)" % (trans.tdo_length, 7))

            if trans.tdi_value != 0:
                print("Error: unexpected TDI value during SLD enumeration: 0x%x" % trans.tdi_value)

            if trans.tdo_value > 15:
                print("Error: TDO value larger than 15 during SLD enumeration: 0x%x" % trans.tdo_value)

            if len(self.enumeration_array) <= self.enumeration_idx:
                # Fill in the value that was sent out
                self.enumeration_array.append(trans.tdo_value)
                self.enumeration_idx += 1

                print("Note: adding 0x%x to enumeration array." % trans.tdo_value)

                if (self.enumeration_idx % 8) == 0:
                    # There are 8 shifts per SLD item.

                    enum_id = 0
                    for i in range(0,8):
                        enum_id += (self.enumeration_array[self.enumeration_idx-8+i] & 0xf) << (i * 4)

                    if self.enumeration_idx == 8:
                        # The first 8 enumeration shifts are to define the SLD hub info
                        self.m_bits         =  enum_id        & 0xff
                        self.hub_mfg_id     = (enum_id >> 8)  & 0xff
                        self.hub_num_nodes  = (enum_id >> 19) & 0xff
                        self.hub_rev        = (enum_id >> 27) & 0x1f
                        self.n_bits         = math.ceil(math.log2(self.hub_num_nodes+1)) 
                        print("Note: new SLD hub : %08x: mfg id: %d, nr nodes: %d, hub rev: %d, m: %d" % (enum_id, self.hub_mfg_id, self.hub_num_nodes, self.hub_rev, self.m_bits))
                        print("Note: VIR length = n(%d) + m(%d) = %d" % ( self.n_bits, self.m_bits, self.n_bits + self.m_bits))

                        # There are 2 VIR chain objects related to SLDHub:
                        # - the one in SLDModel contains both the VIR address and the VIR value for a particular node.
                        # - the one in SLDHub contains only the VIR value
                        new_vir_chain_length = self.m_bits + self.n_bits

                        if self.sld_model.vir_chain.length != new_vir_chain_length:
                            print(str(self.sld_model.vir_chain))
                            print(new_vir_chain_length)
                            print("Error: previous VIR chain length (%d) was wrong." % self.sld_model.vir_chain.length)
                        else:
                            print("Note: previous VIR chain length (%d) matches new length." % self.sld_model.vir_chain.length)

                        self.sld_model.vir_chain.length = self.m_bits + self.n_bits
                        self.vir_chain.length   = self.m_bits
                        self.sld_model.m_bits   = self.m_bits

                    else:
                        inst_id    =  enum_id        & 0xff
                        mfg_id     = (enum_id >> 8)  & 0xff
                        node_id    = (enum_id >> 19) & 0xff
                        rev        = (enum_id >> 27) & 0x1f

                        sld_node = SLDNode.factory(mfg_id, node_id, rev, inst_id, self.sld_model)
                        self.sld_model.sld_nodes[len(self.sld_model.sld_nodes)] = sld_node

                        print("Note: new SLD item: %08x: mfg id: %d, node id: %d, node rev: %d, inst id: %d" % (enum_id, sld_node.mfg_id, sld_node.node_id, sld_node.rev, sld_node.inst_id))
        else:
            print("Error: Unknown SLD HUB VIR value");


SLDNode.KNOWN_SLDs[110*256 +   0] = SLDHub

class SignalTap(SLDNode):

    def name(self):
        return "SignalTap"

SLDNode.KNOWN_SLDs[110*256 +   9] = SignalTap

class JtagUart(SLDNode):

    def __init__(self):
        super().__init__()

        self.vir_chain.length = 1
        self.vdr_chains[1]    = FixedLengthScanChain("Config", length = 15, reset_value = None, read_only = True)

        self.r_fifo_bits    = None
        self.w_fifo_bits    = None
        self.mystery_bit    = None

    def update_vir(self, value):
        super().update_vir(value)

        if value not in [0,1]:
            print("Error: %s unknown VIR assignment! 0x%x" % (self.name(), value))

    def shift_vdr(self, trans):

        if self.vir_chain.value == 0:
            print("Note: JTAG UART Data VDR shift")

            if (trans.tdi_length-3)%10 != 0:
                print("Warn: unexpected TDI length")

            low_mystery_bit = trans.tdi_value & 0x01
            has_next_word = (trans.tdi_value >> 1) & 1

            if has_next_word == 0:
                print("Note: TDI doesn't contain byte stream")
            else:
                rx_bytes = []
                for offset in range(2,trans.tdi_length-9,10): 
                    word = trans.tdi_value >> offset
                    rx_byte_ena     = word & 1
                    rx_byte_value   = (word >> 1) & 0xff
                    has_next_word   = (word >> 9) & 1
    
                    if rx_byte_ena == 1:
                        rx_bytes.append(rx_byte_value)
                        print("Note: JTAG UART RX: 0x%02x (%c)" % (rx_byte_value, chr(rx_byte_value)))

                    if has_next_word != 1:
                        print("Note: has_next_word != 1 (pos: %d)" % (offset+9))

        elif self.vir_chain.value == 1:
            print("Note: JTAG UART Config VDR shift")

            if trans.tdi_length != self.vdr_chains[1].length:
                print("Error: transaction length (%d) doesn't match chain length! (%d)\n" % (trans.tdi_length, self.vdr_chains[1].length))

            if trans.tdi_value == 0x0:
                # Config chain
                r_fifo_bits = (trans.tdo_value >> 5) & 0x0f
                w_fifo_bits = (trans.tdo_value >> 1) & 0x0f
                mystery_bit = trans.tdo_value & 0x01

                if (self.r_fifo_bits is not None) and self.r_fifo_bits != r_fifo_bits:
                    print("Error: read FIFO bits changed (orig: %d, new: %d)" % (self.r_fifo_bits, r_fifo_bits))

                if (self.w_fifo_bits is not None) and self.w_fifo_bits != w_fifo_bits:
                    print("Error: write FIFO bits changed (orig: %d, new: %d)" % (self.w_fifo_bits, w_fifo_bits))

                if (self.mystery_bit is not None) and self.mystery_bit != mystery_bit:
                    print("Error: mystery bit changed (orig: %d, new: %d)" % (self.mystery_bit, mystery_bit))

                self.r_fifo_bits = r_fifo_bits
                self.w_fifo_bits = w_fifo_bits
                self.mystery_bit = mystery_bit

            else:
                super().shift_vdr(trans)

        else:
            super().shift_vdr(trans)

    def name(self):
        return "JTAG UART"

    def __str__(self, indent=0):
        indent_str = ' ' * (4*indent)

        s = ""
        s += super().__str__(indent)
        if self.r_fifo_bits is not None:
            s += indent_str + "    Rd FIFO: %d bits (%d deep)\n" % (self.r_fifo_bits, 1<<self.r_fifo_bits)
        if self.w_fifo_bits is not None:
            s += indent_str + "    Wr FIFO: %s bits (%s deep)\n" % (self.w_fifo_bits, 1<<self.w_fifo_bits)
        if self.mystery_bit is not None:
            s += indent_str + "    mystery: %d\n" % (self.mystery_bit)

        return s

SLDNode.KNOWN_SLDs[110*256 + 128] = JtagUart

# SLDModel contains the fully system-level debug/Virtual JTAG system:
# one SLDHub and multiple SLD nodes
class SLDModel:

    def __init__(self, vir_chain, vdr_chain):

        self.vir_chain = vir_chain
        self.vdr_chain = vdr_chain

        self.sld_nodes = collections.OrderedDict()
        self.sld_nodes[0] = SLDNode.factory(mfg_id = 110, node_id = 0, rev = 0, inst_id = None, sld_model = self)

        self.m_bits = None
        pass

    # the VIR scan chain has 2 parts: the lower m bits are value that can be used by each SLD node 
    # any way it wants, just like a regular IR scan chain.
    # The bits above the lower m bits are an address that selects the desired SLD node or hub. 
    # (Address is 0 the SLD hub.)
    def vir_addr(self):
        return self.vir_chain.value >> self.m_bits

    def vir_value(self):
        return self.vir_chain.value & ((1<<self.m_bits)-1)

    def update_vir(self):

        if self.vir_chain.value == 0: 
            # Select SLD enumeration chain
            # We can't use self.vir_addr() and self.vir_value() yet because m_bits isn't known yet.
            self.sld_nodes[0].update_vir(0)

        else:
            print(str(self))
            print("Note: VIR addr = 0x%x, VIR value = 0x%x" % (self.vir_addr(), self.vir_value()))
            sld_node = self.sld_nodes[self.vir_addr()]
            print("      %s" % sld_node)
            print("      %s" % sld_node.name())

            self.sld_nodes[self.vir_addr()].update_vir(self.vir_value())
        pass

    def shift_vdr(self, trans):
        if self.vir_chain.value == 0:
            self.sld_nodes[0].shift_vdr(trans)
        else:
            self.sld_nodes[self.vir_addr()].shift_vdr(trans)
        pass

    def __str__(self, indent = 0):
        indent_str = ' ' * (4*indent)
        
        s = ""

        s += indent_str + "SLD Model:\n"
        s += indent_str + "=========:\n"
        s += indent_str + "VIR:\n"
        s += self.vir_chain.__str__(indent+1)
        s += indent_str + "    m_bits:      %s\n" % self.m_bits
        if self.m_bits is not None:
            s += indent_str + "    VIR addr:    %d\n" % (self.vir_chain.value >> self.m_bits)

        s += indent_str + "SLD nodes:\n"
        for node in self.sld_nodes.items():
            s += indent_str + "    Node %s:" % (node[0])
            if self.m_bits is not None and self.vir_addr() == node[0]:
                s += "       <<<<< SELECTED"
            s += "\n"
            s += node[1].__str__(indent+2)
            s += "\n"

        return s



class User0ScanChain(ScanChain):

    def __init__(self):

        super().__init__("USER0 - VDR")

        self.sld_model = None

        # There will be many different lengths, depending on which VDR is selected.
        pass

    def shift(self, trans):

        self.sld_model.shift_vdr(trans)
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

    def __str__(self, indent = 0):
        s = super().__str__(indent)

        return s


class IntelFpga(Chip):

    MANUFACTURER_ID = "00001101110"

    # FIXME: get these values from the BSDL file
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

        super().__init__(
                    name = name, 
                    ir_length = 10, 
                    ir_reset_value = IntelFpga.IR_CODES["IDCODE"], 
                    ir_capture_value = 0x155, 
                    idcode = idcode, 
                    idcode_ir = IntelFpga.IR_CODES["IDCODE"])

        user0 = User0ScanChain()
        user1 = User1ScanChain()

        self.sld_model = SLDModel(vdr_chain = user0, vir_chain = user1)
        user0.sld_model = self.sld_model
        user1.sld_model = self.sld_model

        self.dr_chains[ IntelFpga.IR_CODES["USER0"] ] = user0
        self.dr_chains[ IntelFpga.IR_CODES["USER1"] ] = user1

        pass

    def __str__(self, indent = 0):
        indent_str = ' ' * (4*indent)

        s = ""
        s += indent_str + super().__str__(indent)

        s += self.sld_model.__str__(indent)

        return s

class IntelEP2C5(IntelFpga):

    def __init__(self):

        idcode  = int(''.join(("0000", "0010000010110001", IntelFpga.MANUFACTURER_ID, "1")), 2)
        super().__init__(name = "EP2C5", idcode = idcode)
        pass

