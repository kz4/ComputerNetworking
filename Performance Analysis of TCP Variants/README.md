# Performance Analysis of TCP Variants

## High Level Approach:

ex1.tcl, ex2.tcl, ex3.tcl are the three tcl scripts that can be run standalone with parameters on the command line to
 generate result. GeneratePlot is a python script that will automatically generate all the parameters problematically
  by iterating through all the required TCP variants, CBR flow rate, queue size and etc, and output the corresponding
  results in three results folder.

## Challenge:
1. Learning how to script in tcl and understand how ns works.
2. Writing a python script that can pragmatically generate required paramester options and call the tcl scripts from
command line
3. Calculate values such as throughput, latency and packet drop rate, which requires some deeper understanding of
computer networking
4. Learn how to plot using Excel with the results generated from the Python script.

## Code Testing:
We have manually tested by directly running every tcl script with every parameter combination required
as well as running the python script to automatically generate all the combinations. We have also looked at the result
 to make sure the results we have obtained make sense.

Makefile is intentionally left empty
