#!/usr/bin/env bash
#
# thomas@linuxmuster.net
# 20260618
#

/usr/sbin/blkid -t TYPE=ext4 -o device | while read ROOT; do

    echo "Enabling ext4 quota on ${ROOT} "
    /usr/sbin/tune2fs -O quota "$ROOT" || echo "tune2fs: $?"

done
