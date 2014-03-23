The icmpPing.py program can be invoked in the Python command line using:

execfile("icmpPing.py")

* The script must be run with Administrator privileges

Main program can be invoked with one required and two optional parameters:

ping(IPAddr:string, timeout:int, numpings:int)

If the timeout and number of pings are not specified, the default values
are timeout=1s and numpings=4

This program was created based on the skeleton code in pinger-skeleton.txt. Modifications were 
made to the receiveOnePing, sendOnePing, doOnePing, and ping functions.