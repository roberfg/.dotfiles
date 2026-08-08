# ~/.bashrc — portable. Override maquina-especificos en ~/.bashrc.local.
case $- in
    *i*) ;;
      *) return;;
esac

HISTCONTROL=ignoreboth
shopt -s histappend
HISTSIZE=1000
HISTFILESIZE=2000
shopt -s checkwinsize

[ -f ~/.bash_aliases ] && . ~/.bash_aliases
[ -f ~/.bashrc.local ] && . ~/.bashrc.local

# Opencode: limpia modos TUI antes de cada prompt.
__reset_tui() {
    printf '\033[?1000l\033[?1002l\033[?1003l\033[?1006l' >/dev/tty 2>/dev/null
    stty sane >/dev/null 2>&1
}
if [[ ";${PROMPT_COMMAND:-};" != *";__reset_tui;"* ]]; then
    PROMPT_COMMAND="__reset_tui${PROMPT_COMMAND:+; $PROMPT_COMMAND}"
fi
