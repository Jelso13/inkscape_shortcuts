#!/usr/bin/env bash

DIR_TO_SHOW="/tmp/pictures"

SELECTION=$(
    find "$DIR_TO_SHOW" -maxdepth 1 -type f |
    while IFS= read -r imageFile; do
        printf '%s\0icon\x1f%s\n' "$imageFile" "$imageFile"
    done |
    rofi -no-config -theme fullscreen-preview.rasi -dmenu
)
