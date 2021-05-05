#!/bin/bash
#put the .service file in the service directory: /etc/systemd/system/
WD=$(pwd)
cd $WD
source $WD/env/bin/activate
#check every 10 minutes
python3 $WD/upcheck.py -i 600