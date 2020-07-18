

class ScanChain:

    def __init__(self):

        pass


class FixedLengthScanChain(ScanChain):

    def __init__(self, len, reset_value, read_only = False):

        super.__init__()

        self.len            = len
        self.reset_value    = reset_value
        self.value          = reset_value
        self.read_only      = read_only

        pass


class IdCodeScanChain(FixedLengthScanChain):

    def __init__(self, idcode):

        super.__init__(32, idcode, read_only = True)

        pass
        


