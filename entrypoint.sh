#!/bin/sh

# adapted from https://www.arp242.net/tmux.html

set -euC
cd ~/cbc

att() {
    [ -n "${TMUX:-}" ] &&
        tmux -u switch-client -t '=session' ||
        tmux -u attach-session -t '=session'
}

if tmux has-session -t '=session' 2> /dev/null; then
    att
    exit 0
fi

# create session
tmux -u new-session -d -s session

# use send-keys so the pane doesn't close when the program is stopped
tmux -u rename-window 'app'
tmux -u send-keys -t '=session:=app' 'source env/bin/activate; python3 ./bot/start.py' Enter

export FLASK_ENV="development"
tmux -u split-window -h -t '=session:=app' -c web/backend
tmux -u send-keys -t '=session:=app' 'flask run' Enter

att