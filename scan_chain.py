
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

    def __str__(self, indent = 0):
        indent_str = ' ' * (4 * indent)

        s = indent_str + "name:        %s\n" % self.name
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

    # The value that gets captured during the CAPTURE_IR or CAPTURE_DR phase.
    # By default, return the value that was shifted in earlier or that was
    # set during reset.
    # However, some chains return a different value than the value that was shifted
    # in. IR chain is a good example of that.
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
                print("Warn: Unexpected lower TDO value: 0x%x (act) != 0x%x (exp)" % (tdo_masked, capture_value))
            else:
                print("Note: Lower TDO value match! 0x%x" % (capture_value))

        if (trans.tdi_length > self.length):
            # Check that excess bits on TDI appeared on TDO 
            tdi_masked  = trans.tdi_value & ((1<<(trans.tdi_length-self.length))-1)
            tdo_shifted = trans.tdo_value >> self.length

            if tdi_masked != tdo_shifted:
                print("Warn: Unexpected upper TDO value: 0x%x (act) != 0x%x (exp)" % (tdo_shifted, tdi_masked))
            else:
                print("Note: Upper TDO value match! 0x%x" % (tdi_masked))


        if not(self.read_only):
            tdi_shifted = trans.tdi_value >> (trans.tdi_length - self.length)
            print("Action: Update value: 0x%x -> 0x%x" % (self.value, tdi_shifted))
            self.value = trans.tdi_value >> (trans.tdi_length - self.length)

    def __str__(self, indent = 0):

        indent_str = ' ' * (indent * 4)

        s = super().__str__(indent)
        if self.length is None:
            s += indent_str + "length:      Unknown\n"
        else:
            s += indent_str + "length:      %d\n" % self.length

        s += indent_str + "read_only:   %s\n" % self.read_only

        if self.reset_value is None:
            s += indent_str + "reset:       Unknown\n"
        else:
            s += indent_str + "reset:       0x%x\n" % self.reset_value

        if self.value is None:
            s += indent_str + "value:       Unknown\n"
        else:
            if (self.value != -1):
                s += indent_str + "value:       0x%x\n" % self.value
            else:
                s += indent_str + "value:       Unknown\n"

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

class BypassScanChain(FixedLengthScanChain):

    def __init__(self):

        super().__init__("BYPASS", 1, 0)
        pass

    def capture_value(self):
        return 0

