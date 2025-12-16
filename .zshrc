# Path to your Oh My Zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set theme
ZSH_THEME="robbyrussell"

# Enable case-insensitive completion
CASE_SENSITIVE="false"

# Hyphen-insensitive completion. Case sensitive completion must be off.
HYPHEN_INSENSITIVE="true"

# Auto-update behavior
zstyle ':omz:update' mode auto

# Timestamp format in history command
HIST_STAMPS="yyyy-mm-dd"

# Plugins for Python/Docker development with autocomplete
plugins=(
  git
  docker
  docker-compose
  pip
  python
  command-not-found
  sudo
  history
  copypath
  copyfile
  colored-man-pages
  zsh-autosuggestions
  zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

# User configuration

# Enable autocomplete
autoload -Uz compinit
compinit

# Autocomplete options
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}' 'r:|[._-]=* r:|=*' 'l:|=* r:|=*'
zstyle ':completion:*' list-colors ''
zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([0-9]#) ([0-9a-z-]#)*=01;34=0=01'

# History configuration
HISTSIZE=10000
SAVEHIST=10000
setopt HIST_IGNORE_ALL_DUPS
setopt HIST_FIND_NO_DUPS
setopt HIST_SAVE_NO_DUPS
setopt SHARE_HISTORY

# Aliases for Django/Docker development
alias dj="python manage.py"
alias djrun="python manage.py runserver 0.0.0.0:8000"
alias djmig="python manage.py migrate"
alias djmake="python manage.py makemigrations"
alias djshell="python manage.py shell"
alias djtest="pytest"
alias djcov="pytest --cov"
alias dc="docker compose"
alias dcu="docker compose up"
alias dcd="docker compose down"
alias dcr="docker compose restart"
alias dcl="docker compose logs"
alias dce="docker compose exec"

# UV aliases
alias uv-sync="uv sync"
alias uv-add="uv add"
alias uv-run="uv run"

# Enable vi mode (optional - comment out if you prefer emacs mode)
# bindkey -v
