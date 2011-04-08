#!/usr/bin/env bash
source ./virtualenv/bin/activate
set -e
python -mofftrac.dumptrac
python dbmanage.py version_control
python dbmanage.py upgrade
python -mofftrac.etl
