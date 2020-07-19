
import pprint
pp = pprint.PrettyPrinter(indent=4)

class ScanChain:

    def __init__(self, name):
        self.name    = name
        pass

    def __str__(self):

        s   = "%s:\n" % self.name
        return s


class FixedLengthScanChain(ScanChain):

    def __init__(self, name, length, reset_value = None, read_only = False):

        super().__init__(name)

        self.length         = length
        self.reset_value    = reset_value
        self.value          = -1
        self.read_only      = read_only

        pass

    def reset(self):
        if self.reset_value:
            self.value  = self.reset_value

    def shift(self, transaction):

        if self.value:
            tdo_masked = transaction["tdo"] & ((1<<self.length)-1)

            if self.value != tdo_masked:
                print("Unexpected TDO value: %x != %x" % (self.value, tdo_masked))
            else:
                print("TDO value match! %x" % (self.value))


        if not(self.read_only):
            tdi_shifted = transaction["tdi"] >> (transaction["tdi_bits"] - self.length)
            print("%x, %x" % (tdi_shifted, transaction["tdi"]))
            self.value = transaction["tdi"] >> (transaction["tdi_bits"] - self.length)

    def __str__(self):

        s = super().__str__()
        s += "    length:      %d\n" % self.length
        s += "    read_only:   %s\n" % self.read_only
        s += "    reset:       %x\n" % self.reset_value
        s += "    value:       %x\n" % self.value

        return s

class IdCodeScanChain(FixedLengthScanChain):

    def __init__(self, idcode):

        super().__init__("IDCODE", 32, idcode, read_only = True)

        pass

#    def shift_dr(self, transaction):

        
class BypassScanChain(FixedLengthScanChain):

    def __init__(self):

        super().__init__("BYPASS", 1, 0)

        pass

