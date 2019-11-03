#! /usr/bin/env python3

import json
import fileinput
import sys
import getopt

import pprint

pp = pprint.PrettyPrinter(indent=4)

#============================================================

def usage():
    sys.stderr.write(f"Usage: {sys.argv[0]} [options] <BSDL file> <file with boundary scan dump HEX values>\n")
    sys.stderr.write(f"    -r , --rename <file>                  : file with port name renamings\n")


try:
    opts, argv = getopt.getopt(sys.argv[1:], "r:", ["rename="])
except getopt.GetoptError as err:
    print(err)
    usage()
    sys.exit(2)

rename_filename = None

for o, a in opts:
    if o in ("-r", "--rename"):
        rename_filename = a

if len(argv) < 2:
    usage()
    sys.exit(2)

#============================================================

pin_renamings = {}
if rename_filename:
    with open(rename_filename) as rename_file:
        for line in rename_file:
            pin_name, value = line.strip().split(":")
            pin_renamings[pin_name] = value

#============================================================

all_ports = {}
all_bregs_list = []

# Merge all BSDL port and pin data into 1 struct

bsdl_file = argv.pop(0)

with open(bsdl_file) as json_file:
    data = json.load(json_file)
    for log_port_segment in data["logical_port_description"]:
        for port_name in log_port_segment["identifier_list"]:
            all_ports[port_name] = {
                        "pin_type"          : log_port_segment["pin_type"],
                        "port_dimension"    : log_port_segment["port_dimension"],
                        "pin_info"          : {},
                        "bscan_regs"        : []
                    }

    for port2pin in data["device_package_pin_mappings"][0]["pin_map"]:
        all_ports[port2pin["port_name"]]["pin_info"] = port2pin

    fixed_boundary_stmts = data["boundary_scan_register_description"]["fixed_boundary_stmts"]
    bscan_length = int(fixed_boundary_stmts["boundary_length"])

    for bscan_reg in fixed_boundary_stmts["boundary_register"]:
        all_bregs_list.append(bscan_reg)

    for bscan_reg in all_bregs_list:
        port_name = bscan_reg["cell_info"]["cell_spec"]["port_id"]
        bscan_reg["values"] = []
        if port_name != "*":
            all_ports[port_name]["bscan_regs"].append(bscan_reg)

            input_or_disable_spec = bscan_reg["cell_info"]["input_or_disable_spec"]
            if input_or_disable_spec:
                all_ports[port_name]["bscan_regs"].append(all_bregs_list[int(input_or_disable_spec["control_cell"])])


    #pp.pprint(all_ports)
    #print(json.dumps(data, indent=4))


for filename in argv:

    for line in open(filename).readlines():
        line = line.strip()
        if len(line) == 0:
            continue

        if line.strip()[0] == "#":
            continue

        hex_str = line
        breg_val = int(hex_str, 16)

        for port_name in sorted(all_ports.keys()):
            port_info = all_ports[port_name]
            if len(port_info["bscan_regs"]) == 0:
                continue

            for bscan_reg in port_info["bscan_regs"]:
                cell_nr = int(bscan_reg["cell_number"])
                val     = (breg_val >> cell_nr)&1
                bscan_reg["values"].append(val)

#pp.pprint(all_ports)

for port_name in sorted(all_ports.keys()):
    port_info = all_ports[port_name]
    bscan_regs = port_info["bscan_regs"]
    if len(bscan_regs) == 0:
        continue

    pin_name   = port_info["pin_info"]["pin_list"][0]
    renaming   = pin_renamings.get(pin_name, port_name)

    for bscan_reg in bscan_regs:

        dir     = bscan_reg["cell_info"]["cell_spec"]["function"]
        values  = bscan_reg["values"]

        print("{:<5} {:<12}: {:<10}: ".format(pin_name, "("+renaming+")", dir), end=" ")

        all_values = {}
        for val in values:
            all_values[val] = 1
            print(val, end=" ")

        if len(all_values.keys()) > 1:
            print("!", end=" ")

        print()

    print()


