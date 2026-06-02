#!/usr/bin/env bash

if [ -f /mnt/h/AETHIEAOPSYS/ENV/SHELL/aethiea_env.sh ]; then
  # shellcheck source=/mnt/h/AETHIEAOPSYS/ENV/SHELL/aethiea_env.sh
  . /mnt/h/AETHIEAOPSYS/ENV/SHELL/aethiea_env.sh
fi

alias hermes="$AETH_ROOT/TOOLIO/bin/hermes"
alias aeusb="$AETH_ROOT/TOOLIO/bin/aeusb"
