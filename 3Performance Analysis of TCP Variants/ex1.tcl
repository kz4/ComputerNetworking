# Claim, this code uses http://nile.wpi.edu/NS/ as a starting point

# 0) Create a folder ex1_trace: mkdir ex1_trace
# To run this script, increase cbrFlowRate from 1 to 10:
# 1) Tahoe: ns ex1.tcl cbrFlowRate TCP
# 2) Reno: ns ex1.tcl cbrFlowRate TCP/Reno
# 3) NewReno: ns ex1.tcl cbrFlowRate TCP/Newreno
# 4) Vegas: ns ex1.tcl cbrFlowRate TCP/Vegas

# Create a simulator object
set ns [new Simulator]

# Read rate of cbr and variant of tcp from the command line
# Check availbility of inputs
if {$argc != 2} {
        puts "This script requires two parameters as inputs:"
        puts "the first parameter the CBR flow rate"
        puts "the second parameter is a tcp variant"
        exit 1
}

# Define different colors for data flows
$ns color 1 Blue
$ns color 2 Red

# Open the trace file
set file_name ex1_trace/
if {[lindex $argv 1] == "TCP"} {
        append file_name Tahoe_CBR_
} else {
        append file_name [lindex [split [lindex $argv 1] /] 1]_CBR_
}
append file_name [lindex $argv 0].tr
set tf [open $file_name w]
$ns trace-all $tf

# Define a 'finish' procedure
proc finish {} {
        global ns tf
        $ns flush-trace
        #Close the trace file
        close $tf
        exit 0
}

# Create six nodes as the topology
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

# Create links between the nodes using DropTail queue
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n5 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n3 $n4 10Mb 10ms DropTail
$ns duplex-link $n3 $n6 10Mb 10ms DropTail

# Set Queue Size of link (n2-n3) to 10
$ns queue-limit $n2 $n3 10

# Set topology as follows
$ns duplex-link-op $n1 $n2 orient right-down
$ns duplex-link-op $n5 $n2 orient right-up
$ns duplex-link-op $n2 $n3 orient right
$ns duplex-link-op $n4 $n3 orient left-down
$ns duplex-link-op $n6 $n3 orient left-up


# ************************ CBR ************************
# Add a CBR source at n2 as an unresponsive UDP flow
set udp [new Agent/UDP]
$ns attach-agent $n2 $udp
# and add a sink at n3
set sink [new Agent/Null]
$ns attach-agent $n3 $sink
$ns connect $udp $sink

# Setup a CBR over UDP connection
# The CBR flow is the parameter you need to vary for this
# experiment. For example, start the CBR flow at a rate of
# 1 Mbps and record the performance of the TCP flow. Then
# change the CBR flow's rate to 2 Mbps and perform the test
# again. Keep changing the CBR's rate until it reaches the
# bottleneck capacity.
set cbrFlow [lindex $argv 0]
append cbrFlow Mb
set cbr [new Application/Traffic/CBR]
$cbr set rate_ $cbrFlow
$cbr set type_ CBR
$cbr attach-agent $udp
# *********************** CBR ************************


# ************************ TCP ************************
# Create a TCP stream and attach it to node n1
set tempType Agent/
# Concatenate the string to make agent type, e.g. Agent/Tahoe
append tempType [lindex $argv 1]
set tcp [new $tempType]
$ns attach-agent $n1 $tcp
# Create a sink at n4
set sink2 [new Agent/TCPSink]
$ns attach-agent $n4 $sink2
$ns connect $tcp $sink2

# Setup a FTP over TCP connection
set ftp [new Application/FTP]
$ftp attach-agent $tcp
$ftp set type_ FTP
# ************************ TCP ************************


# Schedule events for the CBR and FTP agents
$ns at 0.0 "$cbr start"
$ns at 0.0 "$ftp start"
$ns at 10.0 "$ftp stop"
$ns at 10.0 "$cbr stop"
# Call the finish procedure after 10.1 seconds of simulation time
$ns at 10.1 "finish"

# Run the simulation
$ns run