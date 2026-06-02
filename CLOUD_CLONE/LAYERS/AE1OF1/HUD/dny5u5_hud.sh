# === AE1OF1 HUD :: DNY-5U5 ===

export TERM=xterm-256color
alias ls='ls --color=auto'
alias ll='ls -lah --color=auto'

export LS_COLORS='di=1;31:ln=1;36:ex=1;91:*.sh=1;91:*.py=1;93:*.json=1;95:*.log=1;31'

dny_path() {
  if [[ -n "$AETHIEA" && "$PWD" == "$AETHIEA"* ]]; then
    echo -e "\033[38;5;88mDNY-5U5\033[0m"
  else
    echo "$PWD"
  fi
}

aeth_check() {
  echo "MODE → ${AETHIEA_MODE:-UNK}"
  echo "PATH → ${AETHIEA:-NONE}"
  df -h "$AETHIEA" 2>/dev/null
}

alias aeth-check='aeth_check'

emit() {
  case "$*" in
    "DNY-5U5")
      cd "$AETHIEA/MODS/P47H30N/NODES/DNY-5U5" && ls
      ;;
    "STATUS")
      aeth_check
      ;;
    "ROUTE CORE")
      cd "$AETHIEA/CORE" && ls
      ;;
    "ROUTE DATA")
      cd "$AETHIEA/DATA" && ls
      ;;
    "ROUTE TOOLIO")
      cd "$AETHIEA/TOOLIO" && ls
      ;;
    "MAP SYSTEM")
      find "$AETHIEA" -maxdepth 2 -type d | sort
      ;;
    "LOCATE SELF")
      pwd
      ;;
    "RENDER")
      ls -lah
      ;;
    *)
      echo "UNRESOLVED AETHER → $*"
      ;;
  esac
}

alias AE='emit'

dny() {
  cd "$AETHIEA/MODS/P47H30N/NODES/DNY-5U5" && ls
}

export PS1='\[\e[38;5;88m\]\u\[\e[0m\]@\[\e[1;37m\]\h\[\e[0m\]|\[\e[1;91m\]${AETHIEA_MODE:-UNK}\[\e[0m\]:$(dny_path)\$ '

# canonical node jump (no short alias)
DNY-5U5() {
  cd "$AETHIEA/MODS/P47H30N/NODES/DNY-5U5" && ls
}

# (optional) remove old helper if present
unset -f dny 2>/dev/null


# === DNY-5U5 RESOLVERS ===
alias dny-resolve="$AETHIEA/TOOLIO/dny-resolve"
alias dny-status="$AETHIEA/TOOLIO/dny-resolve status"
alias dny-profile="$AETHIEA/TOOLIO/dny-resolve profile"
alias dny-rabbit="$AETHIEA/TOOLIO/dny-resolve rabbit"
alias dny-routes="$AETHIEA/TOOLIO/dny-resolve routes"

# === USB RUNTIME ===
alias aeth-runtime='bash "$AETHIEA/TOOLIO/aeth-runtime"'

# === PLANE ROUTING ===

plane() {
  bash "$AETHIEA/CORE/ROUTING/resolve_plane.sh" "$1"
}

alias governance='plane GOVERNANCE'
alias media='plane MEDIA'
alias infrastructure='plane INFRASTRUCTURE'
alias identity='plane IDENTITY'
alias continuity='plane CONTINUITY'
alias routes='plane ROUTES'

# === TOOLIO PLANE COMMANDS ===
alias governance='bash "$AETHIEA/TOOLIO/plane" governance'
alias media='bash "$AETHIEA/TOOLIO/plane" media'
alias infrastructure='bash "$AETHIEA/TOOLIO/plane" infrastructure'
alias identity='bash "$AETHIEA/TOOLIO/plane" identity'
alias continuity='bash "$AETHIEA/TOOLIO/plane" continuity'
alias routes='bash "$AETHIEA/TOOLIO/plane" routes'

# === TOOLIO PLANE COMMANDS ===
alias governance='bash "$AETHIEA/TOOLIO/plane" governance'
alias media='bash "$AETHIEA/TOOLIO/plane" media'
alias infrastructure='bash "$AETHIEA/TOOLIO/plane" infrastructure'
alias identity='bash "$AETHIEA/TOOLIO/plane" identity'
alias continuity='bash "$AETHIEA/TOOLIO/plane" continuity'
alias routes='bash "$AETHIEA/TOOLIO/plane" routes'

# === OPERATOR RESOLUTION ===
alias operator-resolve='bash "$AETHIEA/TOOLIO/operator-resolve"'
