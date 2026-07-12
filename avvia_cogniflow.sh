#!/bin/bash
# Avviatore CogniFlow - Assistente DSA
cd "$(dirname "$(readlink -f "$0")")" || exit 1
exec python3 -m assistente_dsa "$@"
