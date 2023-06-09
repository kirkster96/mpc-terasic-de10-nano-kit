#!bin/bash
#-------------------------------------------------------------------------------
# Change into the directory of this script
#-------------------------------------------------------------------------------
cd $(dirname "${0:?}")

#-------------------------------------------------------------------------------
# Verify tool requirements
#-------------------------------------------------------------------------------
type -P \
	quartus_sh \
	sopc-create-header-files \
	qsys-generate \
	qsys-script \
> /dev/null || {
	echo ""
	echo "ERROR: could not locate all required tools in environment"
	echo ""
	exit 1
}

#-------------------------------------------------------------------------------
# Display the tools environment
#-------------------------------------------------------------------------------
cat << EOF

This example was tested with this version of the Quartus Prime software:

Quartus Prime Shell
Version 17.0.0 Build 595 04/25/2017 SJ Standard Edition
Copyright (C) 2017  Intel Corporation. All rights reserved.

If your tools are not from this version you may experience build issues related
to those version differences.

Your tool version appears to be:

EOF

quartus_sh --version || { echo "ERROR" ; exit 1 ; }

echo


#-------------------------------------------------------------------------------
# Create 'blink' project directory relative to this script
#-------------------------------------------------------------------------------
[ -d "blink" ] && {
	echo ""
	echo "ERROR: directory 'blink' already exists"
	echo ""
	exit 1
}

mkdir blink || { echo "ERROR" ; exit 1 ; }
cd blink || { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Copy blink.v source file into project build directory
#-------------------------------------------------------------------------------
[ -f "../hdl_src/blink.v" ] || {
	echo ""
	echo "ERROR: cannot locate source file"
	echo "'hdl_src/blink.v'"
	echo ""
	exit 1
}

cp ../hdl_src/blink.v . || { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Copy blink.sdc source file into project build directory
#-------------------------------------------------------------------------------
[ -f "../hdl_src/blink.sdc" ] || {
	echo ""
	echo "ERROR: cannot locate source file"
	echo "'hdl_src/blink.sdc'"
	echo ""
	exit 1
}

cp ../hdl_src/blink.sdc . || { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Create the Qsys system
#-------------------------------------------------------------------------------
[ -f "../scripts/create_qsys_system_soc_system.tcl" ] || {
	echo ""
	echo "ERROR: cannot locate source file"
	echo "'scripts/create_qsys_system_soc_system.tcl'"
	echo ""
	exit 1
}

qsys-script --script="../scripts/create_qsys_system_soc_system.tcl" \
|| { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Generate the Qsys system
#-------------------------------------------------------------------------------
qsys-generate soc_system.qsys --synthesis=VERILOG --part=5CSEBA6U23I7 \
|| { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Generate C headers for all Qsys masters
#-------------------------------------------------------------------------------
mkdir qsys_headers || { echo "ERROR" ; exit 1 ; }
sopc-create-header-files soc_system.sopcinfo --output-dir qsys_headers \
|| { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Create the quartus project
#-------------------------------------------------------------------------------
[ -f "../scripts/create_quartus_project.tcl" ] || {
	echo ""
	echo "ERROR: cannot locate source file"
	echo "'scripts/create_quartus_project.tcl'"
	echo ""
	exit 1
}

quartus_sh --script="../scripts/create_quartus_project.tcl" \
|| { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Compile the quartus project
#-------------------------------------------------------------------------------
quartus_sh --flow compile blink || { echo "ERROR" ; exit 1 ; }

#-------------------------------------------------------------------------------
# Program the fpga
#-------------------------------------------------------------------------------
echo "To program the FPGA via JTAG, use this command:"
echo "quartus_pgm -m jtag -c 1 -o \"p;output_files/blink.sof@2\""

exit 0

