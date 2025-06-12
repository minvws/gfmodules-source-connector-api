#!/usr/bin/env bash

set -e

echo "➡️ Generating TLS certificates"
tools/./generate_certs.sh

echo "➡️ Creating the configuration file"
if [ -e app.conf ]; then
    echo "⚠️ Configuration file already exists. Skipping."
else
    cp app.conf.autopilot app.conf
fi

echo "Start main process"
python -m app.main
