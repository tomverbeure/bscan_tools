
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

    def __init__(self, name, length, reset_value, read_only = False):

        super().__init__(name)

        self.length         = length
        self.reset_value    = reset_value
        self.value          = reset_value
        self.read_only      = read_only

        pass

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
        
class BypassScanChain(FixedLengthScanChain):

    def __init__(self):

        super().__init__("BYPASS", 1, 0)

        pass

