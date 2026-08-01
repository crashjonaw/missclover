#!/usr/bin/env bash
# Local dev — delegates to run.sh
exec "$(dirname "$0")/run.sh" "$@"
