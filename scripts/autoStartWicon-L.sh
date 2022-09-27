#!/bin/bash

while [ 1 ]
   do
        pid=`ps -ef | grep "wicon_lite_main.py" | grep -v 'grep' | awk '{print $2}'`
        if [ -z $pid ]; then
	 cd /home/pi/Wicon-L-Py/scripts/
	 sh reStartWicon-L.sh
        fi
       sleep 10
   done
