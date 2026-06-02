# RUBIII — AETHIEAOPSYS surface prompt
# High-contrast red background / black-white foreground

BG_RED="\[\033[41m\]"
BG_BRIGHT_RED="\[\033[101m\]"
FG_WHITE="\[\033[1;37m\]"
FG_BLACK="\[\033[1;30m\]"
FG_YELLOW="\[\033[1;33m\]"
RESET="\[\033[0m\]"

export PS1="${BG_RED}${FG_WHITE} \u@RUBIII ${RESET}${BG_BRIGHT_RED}${FG_BLACK} USB_CONTINUITY ${RESET}${BG_RED}${FG_YELLOW} DNY-5U5 ${RESET} \$ "
