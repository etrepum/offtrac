#!/usr/bin/env python
from migrate.versioning.shell import main
main(url='sqlite:///offtrac.db', debug='False', repository='dbrepo')
