#! /usr/bin/env bash

script_path=$(dirname "$0")
root_path=$script_path/..

cd $root_path

function setupVirtualEnv() {
    # Create virtualenv folder if missing
    cd $root_path
    if [ ! -d python-venv ]
    then
        echo "Setting up new virtualenv..."
        python3 -m venv python-venv || exit 1
    fi

    # Install or update dependencies
    source python-venv/bin/activate || exit 1
    pip install --upgrade --quiet pip
    pip install -r $script_path/requirements.txt --upgrade --quiet
    deactivate
}

# Setup virtualenv
setupVirtualEnv

# Activate virtualenv
source $root_path/python-venv/bin/activate || exit 1

# Running main script
python $script_path/check_en_differences.py $@

# Reformat resulting JSON
python $script_path/reformat_json.py
