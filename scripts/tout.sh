#!/bin/bash
#打开日志

cd `dirname $0`/..
export BASE_DIR=`pwd`
echo $BASE_DIR

# check the nohup.out log output file
if [ ! -f "${BASE_DIR}/nohup.out" ]; then
   echo "No file  ${BASE_DIR}/nohup.out"
   exit -1;
fi

tail -f "${BASE_DIR}/nohup.out"
