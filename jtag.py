
import pprint
pp = pprint.PrettyPrinter(indent=4)

class JtagState:

    TEST_LOGIC_RESET    = 0
    RUN_TEST_IDLE       = 1
    SELECT_DR_SCAN      = 2
    CAPTURE_DR          = 3
    SHIFT_DR            = 4
    EXIT1_DR            = 5
    PAUSE_DR            = 6
    EXIT2_DR            = 7
    UPDATE_DR           = 8
    SELECT_IR_SCAN      = 9
    CAPTURE_IR          = 10
    SHIFT_IR            = 11
    EXIT1_IR            = 12
    PAUSE_IR            = 13
    EXIT2_IR            = 14
    UPDATE_IR           = 15

    STATE_LOOKUP = {
            "Test-Logic-Reset"  :    TEST_LOGIC_RESET,
            "Run-Test/Idle"     :    RUN_TEST_IDLE,
            "Select-DR-Scan"    :    SELECT_DR_SCAN,
            "Capture-DR"        :    CAPTURE_DR,
            "Shift-DR"          :    SHIFT_DR,
            "Exit1-DR"          :    EXIT1_DR,
            "Pause-DR"          :    PAUSE_DR,
            "Exit2-DR"          :    EXIT2_DR,
            "Update-DR"         :    UPDATE_DR,
            "Select-IR-Scan"    :    SELECT_IR_SCAN,
            "Capture-IR"        :    CAPTURE_IR,
            "Shift-IR"          :    SHIFT_IR,
            "Exit1-IR"          :    EXIT1_IR,
            "Pause-IR"          :    PAUSE_IR,
            "Exit2-IR"          :    EXIT2_IR,
            "Update-IR"         :    UPDATE_IR,
    }

    STATE_STR = {
            TEST_LOGIC_RESET    : "Test-Logic-Reset",
            RUN_TEST_IDLE       : "Run-Test/Idle",
            SELECT_DR_SCAN      : "Select-DR-Scan",
            CAPTURE_DR          : "Capture-DR",
            SHIFT_DR            : "Shift-DR",
            EXIT1_DR            : "Exit1-DR",
            PAUSE_DR            : "Pause-DR",
            EXIT2_DR            : "Exit2-DR",
            UPDATE_DR           : "Update-DR",
            SELECT_IR_SCAN      : "Select-IR-Scan",
            CAPTURE_IR          : "Capture-IR",
            SHIFT_IR            : "Shift-IR",
            EXIT1_IR            : "Exit1-IR",
            PAUSE_IR            : "Pause-IR",
            EXIT2_IR            : "Exit2-IR",
            UPDATE_IR           : "Update-IR",
    }

    def __init__(self):

        pass

class JtagTransaction:

    def __init__(self):

        self.nr             = None
        self.time           = None
        self.state          = None
        self.tdi_value      = None
        self.tdi_length     = None
        self.tdo_value      = None
        self.tdo_length     = None

        pass

    def __str__(self):

        s = ""

        s += "%d: %s" % (self.nr, JtagState.STATE_STR[self.state])

        if self.state in (JtagState.SHIFT_DR, JtagState.SHIFT_IR):
            tdi_str = ("%x" % self.tdi_value).zfill((self.tdi_length+3) // 4)
            tdo_str = ("%x" % self.tdo_value).zfill((self.tdo_length+3) // 4)
            s += " - TDI %s - TDO %s - %d" % (tdi_str, tdo_str, self.tdo_length)
        s+= "\n"

        return s

    # Read a Saleae JTAG decoded file that was saved as CSV and return a list of JTAG transactions.
    def read_saleae_jtag_csv(jtag_csv_filename):
        transactions = []

        # Saleae JTAG CSV files store TDI and TDO data in 2 different formats, depending
        # on how long the data is.
        #     Short format: 0x155
        #     Long format:  [0x0FECC0FF020B10DD], [0xFFFFFFFFFFFFFFFF], [0x1]
        # Convert it a simple integer...
        def convert_tdi_tdo_str(str):

            val = 0
        
            str_segments = str.split(",")
            if len(str_segments) == 1:
                val = int(str_segments[0][2:], 16)
            else: 
                val = 0
                start_bit = 0
                for segment in str_segments:
                    segment_val = int(segment.strip()[3:-1], 16) << start_bit
                    val += segment_val
                    start_bit += 64
        
            return val
    
        with open(jtag_csv_filename) as jtag_file:
            first_line = True
    
            for line_num, line in enumerate(jtag_file):
                if first_line:
                    first_line = False
                    continue 
    
                time, tap_state, tdi, tdo, tdi_bits, tdo_bits = line.strip().split(";")
    
                time = float(time)
    
                if tap_state in JtagState.STATE_LOOKUP:
                    tap_state_nr    = JtagState.STATE_LOOKUP[tap_state]
    
                if tdi_bits != "":
                    tdi_bits = int(tdi_bits)
                else:
                    tdi_bits = 0
    
                if tdo_bits != "":
                    tdo_bits = int(tdo_bits)
                else:
                    tdo_bits = 0
    
                if tdi != "": 
                    tdi = convert_tdi_tdo_str(tdi)
                else:
                    tdi = None
    
                if tdo != "": 
                    tdo = convert_tdi_tdo_str(tdo)
                else:
                    tdo = None
    
                #print(time, tap_state_nr, tap_state, tdi_bits, tdi, tdo_bits, tdo)
    
                trans = JtagTransaction()
                trans.nr            = line_num
                trans.time          = time
                trans.state         = tap_state_nr
                trans.tdi_value     = tdi
                trans.tdi_length    = tdi_bits
                trans.tdo_value     = tdo
                trans.tdo_length    = tdo_bits
    
                transactions.append(trans)
    
        return transactions



