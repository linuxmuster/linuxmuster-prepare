#!/usr/bin/env bash
#
# thomas@linuxmuster.net
# 20260615
#

install_items+=" /usr/sbin/tune2fs "

check() {
    return 0
}

depends() {
    echo "base"
    return 0
}

install() {
    inst_hook pre-mount 50 "$moddir/pre-mount-lmn.sh"
}
