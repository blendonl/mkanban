#!/usr/bin/env bash

all_sessions=$(tmux list-sessions 2>/dev/null)

attached_sessions=$(echo "$all_sessions" | grep "(attached)" | cut -d':' -f1)

if [ -z "$attached_sessions" ]; then
    selected_name=0    
else 
    session_count=$(echo "$attached_sessions" | wc -l)

    if [ "$session_count" -eq 1 ]; then

        selected_name=$(tmux run "tmux display-message -p '#S'")
        selected_path=$(tmux run "tmux display-message -p '#{pane_current_path}'")

    else
        selected_session=$(echo "$attached_sessions" | fzf --prompt="Select attached tmux session: ")
        
        if [ -n "$selected_session" ]; then
            selected_name=$(tmux run  "tmux -t $selected_session display-message -p '#S'")
            selected_path=$(tmux run  "tmux -t $selected_session display-message -p '#{pane_current_path}'")

        else
            echo "No session selected"
            exit 1
        fi
    fi
fi

if [[ "$selected_path" == *"work"* ]]; then
    selected="$NOTE_PATH/work${selected_path##*work}"
elif [[ "$selected_path" == *"personal"* ]]; then
    selected="$NOTE_PATH/personal${selected_path##*personal}"
elif [[ "$selected_name" =~ ^[0-9]+$ ]]; then
    selected="$NOTE_PATH/general/"
else 
    selected="$NOTE_PATH/general/$selected_name"
fi

path="$selected";

mkdir -p $path
/mnt/data/personal/mkanban/dist/mkanban --data-dir $path --new-item --board "default"











