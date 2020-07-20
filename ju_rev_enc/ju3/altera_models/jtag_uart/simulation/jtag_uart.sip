set_global_assignment -entity "jtag_uart" -library "lib_jtag_uart" -name IP_TOOL_NAME "Qsys"
set_global_assignment -entity "jtag_uart" -library "lib_jtag_uart" -name IP_TOOL_VERSION "13.0sp1"
set_global_assignment -entity "jtag_uart" -library "lib_jtag_uart" -name IP_TOOL_ENV "Qsys"
set_global_assignment -library "lib_jtag_uart" -name SPD_FILE [file join $::quartus(sip_path) "../../jtag_uart.spd"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "../../jtag_uart.qsys"]

set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "jtag_uart.v"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "submodules/altera_reset_controller.v"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "submodules/altera_reset_synchronizer.v"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "submodules/altera_reset_controller.sdc"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "submodules/jtag_uart_jtag_uart_w32_r8.v"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "submodules/jtag_uart_jtag_uart_w8_r64.v"]
set_global_assignment -library "lib_jtag_uart" -name MISC_FILE [file join $::quartus(sip_path) "submodules/jtag_uart_jtag_uart_w16_r32.v"]
