#!/usr/bin/env bash
source ./virtualenv/bin/activate
python -mofftrac.dumptrac && python -mofftrac.etl
