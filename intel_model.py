
import scan_chain

class IntelFpga:

    def __init__(self):

        self.ir         = FixedLengthScanChain()
        self.idcode     = IdCodeScanChain()

