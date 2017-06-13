#!/usr/bin/env python3

import lirc
import time
import requests

sockid = lirc.init("tent-ir", blocking=False)

while True:
    codeIR = lirc.nextcode()
    if not codeIR:
        continue
    codeIR = codeIR[0]

    try:
        if codeIR == "vol-up":
            r = requests.get('http://localhost:8080/music/volup')
        elif codeIR == "vol-down":
            r = requests.get('http://localhost:8080/music/voldown')
        elif codeIR == "next-song":
            r = requests.get('http://localhost:8080/music/next')
        elif codeIR == "next-effect":
            print("Not implemented yet: " + codeIR)
        elif codeIR != []:
            print(codeIR[0])
        time.sleep(0.05)
    except Exception as e:
        print(e)
