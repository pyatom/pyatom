#!/bin/bash
CL=$@
CL=${CL/"-arch i386"}
CL=${CL/"-arch x86_64"}
/usr/bin/gcc $CL
