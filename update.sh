#!/usr/bin/env bash
source ./virtualenv/bin/activate
set -e
python -mofftrac.dumptrac
set +e
python dbmanage.py upgrade
set -e
if [ $? != 0 ]; then
    python dbmanage.py version_control
    python dbmanage.py upgrade
fi
python -mofftrac.etl
