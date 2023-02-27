#!/bin/bash
#打开日志

export BASE_DIR=`pwd`
echo $BASE_DIR

tail -f "${BASE_DIR}/nohup.out"
