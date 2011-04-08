#!/usr/bin/env python
from migrate.versioning.shell import main
from offtrac.etl import get_engine_url
main(url=get_engine_url(), debug='False', repository='dbrepo')
