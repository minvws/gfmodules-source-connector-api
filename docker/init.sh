#!/usr/bin/env bash

set -e

echo "➡️ Creating the configuration file"
if [ -e app.conf ]; then
    echo "⚠️ Configuration file already exists. Skipping."
else
    cp app.conf.example app.conf
fi

echo "Start main process"
python -m app.main
