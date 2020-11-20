#! /usr/bin/env python3

import json
import fileinput
import sys
import argparse
import os
import subprocess
import logging
import appdirs
 

import pprint

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


pp = pprint.PrettyPrinter(indent=4)


parser = argparse.ArgumentParser(description="Parse and visualize openocd's BSCAN data.")
parser.add_argument('bsdl_file', nargs=1, help='Path to BSDL file.')
parser.add_argument('oocd_hex_dump', nargs='+', help='File with boundary scan dump HEX values.')
parser.add_argument('-r', '--rename', default=None, help='File with port name renamings')
parser.add_argument('--bsdl-cache', default=None, help='Path to store parsed bsdl-files.')
args = parser.parse_args()

rename_filename = args.rename
bsdl_file = args.bsdl_file[0]
oocd_hex_dump_files = args.oocd_hex_dump


#============================================================

pin_renamings = {}
if rename_filename:
    with open(rename_filename) as rename_file:
        for line in rename_file:
            if len(line.strip()) == 0 or line.strip()[0] == "#":
                continue
            pin_name, value = line.split(":")
            pin_renamings[pin_name.strip()] = value.strip()

#============================================================

all_ports = {}
all_bregs_list = []

# Merge all BSDL port and pin data into 1 struct

try:
    # Try to open as bsdl-json-file:
    with open(bsdl_file) as json_file:
        data = json.load(json_file)
except json.decoder.JSONDecodeError:
    # bsdl_file is an original BSDL file. Let's find in the cache:
    logging.info(f"{bsdl_file} is not a json file... Lets's find in the cache")
    bname = os.path.basename(bsdl_file)
    cachedir = appdirs.user_cache_dir("bscan_proc") 
    if args.bsdl_cache:
        cachedir = args.bsdl_cache
    try:
        os.mkdir(cachedir)
    except FileExistsError:
        pass
    cached_bsdl_json_file = os.path.abspath(os.path.join(cachedir, f'{bname}.json'))
    if not os.path.isfile(cached_bsdl_json_file):
        logging.info(f"{cached_bsdl_json_file} not found in cache... Lets's parse original.")
        # This original BSDL file has not been parsed yet...
        cmdlist = ['bsdl2json', bsdl_file, '-o', cached_bsdl_json_file]
        logging.info(f"{' '.join(cmdlist)} From: '../python-bsdl-parser'")
        p = subprocess.Popen(cmdlist, cwd='../python-bsdl-parser')
        p.wait()
        
    with open(cached_bsdl_json_file) as json_file:
        logging.info(f"{cached_bsdl_json_file} json has found in the cace.")
        data = json.load(json_file)

#
# Fetch IDCODE, instruction length, and instruction opcodes.
#

# Based on https://stackoverflow.com/a/3495395/2506522
data['optional_register_description'] = {k: v for d in data['optional_register_description'] for k, v in d.items()}
id_code = ''.join(data['optional_register_description']['idcode_register'])
logging.debug(f'IDCODE: {id_code}')
ir_length = data['instruction_register_description']['instruction_length']
logging.debug(f'IRLENGTH: {ir_length}')
data['instruction_register_description']['instruction_opcodes'] = {d['instruction_name']: ''.join(d['opcode_list']) for d in data['instruction_register_description']['instruction_opcodes']}
instruction_opcodes = data['instruction_register_description']['instruction_opcodes']

logging.debug('OPCODES:')
for instr, opcode in instruction_opcodes.items():
    logging.debug(f'  {instr}: {opcode}')

#
# Generate device TCL
#

bname = os.path.basename(bsdl_file)
device_name = os.path.splitext(bname)[0]
tcl_dev_file_content = []
tcl_dev_file_content += [f'# Generated with bscan_proc from {bsdl_file}']

tcl_dev_file_content += ['']
tcl_dev_file_content += ['# ID code']
tcl_dev_file_content += [f'set {device_name}_IDCODE {id_code}']

tcl_dev_file_content += ['']
tcl_dev_file_content += ['# Instruction length']
tcl_dev_file_content += [f'set {device_name}_IRLEN {ir_length}']

tcl_dev_file_content += ['']
tcl_dev_file_content += ['# Instruction opcodes']
for instr, opcode in instruction_opcodes.items():
    tcl_dev_file_content += [f'set {device_name}_{instr} {opcode}']

tcl_dev_file_name = f'{device_name}_dev.tcl'
with open(tcl_dev_file_name, 'w') as tcl_dev_file:
    tcl_dev_file.write(os.linesep.join(tcl_dev_file_content))



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


for filename in oocd_hex_dump_files:

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


# Sort by renamed ports to keep ports with same name together
all_renamed_ports = {}
for port_name in all_ports.keys():
    port_info       = all_ports[port_name]
    pin_name        = port_info["pin_info"]["pin_list"][0]
    renamed_port    = pin_renamings.get(pin_name, port_name)

    all_renamed_ports[renamed_port] = port_name

for renamed_port in sorted(all_renamed_ports.keys()):
    port_name = all_renamed_ports[renamed_port]
    port_info = all_ports[port_name]

    bscan_regs = port_info["bscan_regs"]
    if len(bscan_regs) == 0:
        continue

    pin_name   = port_info["pin_info"]["pin_list"][0]
    renaming   = pin_renamings.get(pin_name, port_name)

    for bscan_reg in bscan_regs:

        dir     = bscan_reg["cell_info"]["cell_spec"]["function"]
        values  = bscan_reg["values"]

        print("{:<5} {:<20}: {:<10}: ".format(pin_name, "("+renaming+")", dir), end=" ")

        all_values = {}
        for val in values:
            all_values[val] = 1
            print(val, end=" ")

        if len(all_values.keys()) > 1:
            print("!", end=" ")

        print()

    print()
