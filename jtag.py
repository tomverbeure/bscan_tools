
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

    def __init__(self):

        pass

