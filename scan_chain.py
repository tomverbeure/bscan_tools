
import pprint
pp = pprint.PrettyPrinter(indent=4)

class ScanChain:

    def __init__(self, name):
        self.name    = name
        pass

    def reset(self):
        pass

    def shift(self, trans):
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
        if self.reset_value is not None:
            self.value  = self.reset_value

    def capture_value(self):
        return self.value

    def shift(self, trans):

        if self.length is None:
            print("Warning: shift into undefined scan chain.")
            return

        capture_value = self.capture_value()

        if self.value:
            tdo_masked = trans.tdo_value & ((1<<self.length)-1)

            if capture_value != tdo_masked:
                print("Unexpected lower TDO value: %x (act) != %x (exp)" % (tdo_masked, capture_value))
            else:
                print("Lower TDO value match! %x" % (capture_value))

        if (trans.tdi_length > self.length):
            # Check that excess bits on TDI appeared on TDO 
            tdi_masked  = trans.tdi_value & ((1<<(trans.tdi_length-self.length))-1)
            tdo_shifted = trans.tdo_value >> self.length

            if tdi_masked != tdo_shifted:
                print("Unexpected upper TDO value: %x (act) != %x (exp)" % (tdo_shifted, tdi_masked))
            else:
                print("Upper TDO value match! %x" % (tdi_masked))


        if not(self.read_only):
            tdi_shifted = trans.tdi_value >> (trans.tdi_length - self.length)
            print("Update value: %x -> %x" % (self.value, tdi_shifted))
            self.value = trans.tdi_value >> (trans.tdi_length - self.length)

    def __str__(self):

        s = super().__str__()
        if self.length is None:
            s += "    length:      Unknown\n"
        else:
            s += "    length:      %d\n" % self.length
        s += "    read_only:   %s\n" % self.read_only
        s += "    reset:       %x\n" % self.reset_value
        s += "    value:       %x\n" % self.value

        return s

class IrScanChain(FixedLengthScanChain):

    def __init__(self, length, reset_value, capture_value):

        super().__init__("IR", length, reset_value, read_only = False)

        self.cap_value = capture_value

        pass

    def capture_value(self):
        return self.cap_value

class IdCodeScanChain(FixedLengthScanChain):

    def __init__(self, idcode):

        super().__init__("IDCODE", 32, idcode, read_only = True)

        pass

#    def shift_dr(self, transaction):

        
class BypassScanChain(FixedLengthScanChain):

    def __init__(self):

        super().__init__("BYPASS", 1, 0)

        pass

    def capture_value(self):
        return 0

