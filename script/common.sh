#!/usr/bin/env bash
# Shared by every script/* verb: pick the venv's python if script/setup has
# made one, otherwise fall back to whatever python3 CI's setup-python put
# on PATH. Keeps the scripts identical in both environments.
if [ -f .venv/bin/python ]; then
  PYTHON=.venv/bin/python
elif [ -f .venv/Scripts/python.exe ]; then
  PYTHON=.venv/Scripts/python.exe
else
  PYTHON=python3
fi
export DB_PATH="${DB_PATH:-data/dev.sqlite}"
