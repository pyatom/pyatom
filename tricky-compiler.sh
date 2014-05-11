#!/bin/bash
CL=$@
CL=${CL/"-arch i386"}
CL=${CL/"-arch x86_64"}
#echo $CL "-arch i386 -arch x86_64 -arch asdf"
/usr/bin/gcc $CL
