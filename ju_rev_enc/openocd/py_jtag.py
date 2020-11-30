#! /usr/bin/env python3

import telnetlib
import math

import pprint
pp = pprint.PrettyPrinter(indent=4)

class JtagMaster:

    def __init__(self, tap, host="localhost", port=4444):

        self.tap        = tap
        self.hostname   = host
        self.port       = port

        self.telnet = telnetlib.Telnet(host, port)
        self.get_results()

    def get_results(self):
        s = self.telnet.read_until(b'>').decode('ascii')
        lines = s.split("\n")
        #pp.pprint(lines)
        return lines[1:-1]


    def scan_init(self):
        self.telnet.write("jtag init\n".encode('ascii'))
        self.get_results()

    def names(self):
        cmd = "jtag names\n"
        self.telnet.write(cmd.encode('ascii'))
        self.get_results()

    def ir_scan(self, value):
        cmd = "irscan %s %d \n" % (self.tap, value)
        self.telnet.write(cmd.encode('ascii'))
        self.get_results()

    def dr_scan(self, value, length):
        cmd = "drscan %s %d %d\n" % (self.tap, length, value)
        self.telnet.write(cmd.encode('ascii'))
        r = int(self.get_results()[0].strip(), 16)
        return r

class SLDNode:

    def __init__(self, sld_hub):
        self.mfg_id         = None
        self.node_id        = None
        self.rev            = None
        self.inst_id        = None
        self.addr           = None

        self.sld_hub        = sld_hub

    def vir_scan(self, value):
        r = self.sld_hub.vir_scan(self.addr, value)
        return r

    def vdr_scan(self, value, length):
        r = self.sld_hub.vdr_scan(self.addr, value, length)
        return r

    def __str__(self, indent=0):
        indent_str = ' ' * (indent * 4)

        s = ""
        s += indent_str + "mfg id: %d, node id: %d, rev id: %d, inst id: %d" % (self.mfg_id, self.node_id, self.rev, self.inst_id)

        return s


class SLDHub:

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

    def __init__(self, jtag):
        self.jtag = jtag
        self.sld_nodes = []

    def vir_scan(self, addr, value):
        self.jtag.ir_scan(SLDHub.IR_CODES['USER1'])
        self.jtag.dr_scan( (addr << self.hub_m_bits) | (value), self.hub_n_bits + self.hub_m_bits)

    def vdr_scan(self, addr, value, length):
        self.jtag.ir_scan(SLDHub.IR_CODES['USER0'])
        r = self.jtag.dr_scan(value, length)
        return r

    def enumerate(self):
        self.jtag.ir_scan(SLDHub.IR_CODES['USER1'])
        self.jtag.dr_scan(0x0, 32)

        self.jtag.ir_scan(SLDHub.IR_CODES['USER0'])

        # Fetch HUB IP Configuration Register
        enum_id = 0
        for i in range(8):
            enum_id = enum_id | self.jtag.dr_scan(0x0, 7) << (i*4)

        self.hub_m_bits         =  enum_id        & 0xff
        self.hub_mfg_id         = (enum_id >>  8) & 0x7ff
        self.hub_num_nodes      = (enum_id >> 19) & 0xff
        self.hub_rev            = (enum_id >> 27) & 0x1f
        self.hub_n_bits         = math.ceil(math.log2(self.hub_num_nodes+1)) 

        print(str(self))
        print("Note: VIR length = n(%d) + m(%d) = %d" % ( self.hub_n_bits, self.hub_m_bits, self.hub_n_bits + self.hub_m_bits))

        for node in range(self.hub_num_nodes):

            # Fetch SLD_NODE Info register
            enum_id = 0
            for i in range(0,8):
                enum_id = enum_id | self.jtag.dr_scan(0x0, 7) << (i*4)

            s = SLDNode(self)
            s.inst_id  =  enum_id        & 0xff
            s.mfg_id   = (enum_id >> 8)  & 0xff
            s.node_id  = (enum_id >> 19) & 0xff
            s.rev      = (enum_id >> 27) & 0x1f
            s.addr     = len(self.sld_nodes)+1
            print(str(s))

            self.sld_nodes.append(s)

    def __str__(self, indent=0):
        indent_str = ' ' * (4*indent)

        s = ""
        s += indent_str + "SLD hub: mfg id: %d, nr nodes: %d, hub rev: %d, m: %d" % (self.hub_mfg_id, self.hub_num_nodes, self.hub_rev, self.hub_m_bits)

        return s

class JtagUart:

    def __init__(self, sld_node):
        self.sld_node       = sld_node
        pass

    def fetch_params(self, tdi=0):
        self.sld_node.vir_scan(1)
        r = self.sld_node.vdr_scan(tdi, 15)
        print("0x%x" % r)

        self.r_fifo_bits = (r >> 5) & 0x0f
        self.w_fifo_bits = (r>> 1) & 0x0f
        self.mystery_bit =  r & 0x01

        print(str(self))
        pass

    def __str__(self, indent=0):
        indent_str = ' ' * (indent * 4)

        s = ""
        s += indent_str + "JtagUart:\n"
        s += indent_str + "    Rd FIFO bits: %d\n" % self.r_fifo_bits
        s += indent_str + "    Wr FIFO bits: %d\n" % self.w_fifo_bits
        s += indent_str + "    mystery bit:  %d\n" % self.mystery_bit

        return s

if __name__ == "__main__":


    j = JtagMaster("ep2c5.tap")
    sld = SLDHub(j)

    j.scan_init()
    j.names()
    sld.enumerate()

    uart = JtagUart(sld.sld_nodes[0])
    uart.fetch_params()

