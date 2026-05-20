#!/bin/sh
set -e

# exec replaces the shell: uvicorn becomes PID 1 and receives signals directly.
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
