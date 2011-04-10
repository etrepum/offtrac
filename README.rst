Offtrac
-------

In order to have any hope of using this, you need a Trac instance with
`Trac XML-RPC Plugin <http://trac-hacks.org/wiki/XmlRpcPlugin>`_ installed.

That said, you probably shouldn't use this. Not yet.

The only usable part is probably the wrapper for the API in
``offtrac.dumptrac``, but this will move to a more sensible module name.

Tools
=====

What this does right now:

``offtrac.dumptrac``:

* Runs with ``python -mofftrac.dumptrac``
* Requires simplejson
* Create a folder ``'./db'`` (see `JSON File Database`_) and initialize it
  as a git repository and make an initial commit.
* Connect to the Trac instance and sync everything to this database as
  JSON files. For changelogs and tickets, it will only download the
  changes since the last sync (but may re-download the latest change).
* Commit the changes to the repository.


``dbmanage.py``:

* Manages the sqlite3 database schema (``./db/offtrac.db``)
* Requires SQLAlchemy, SQLALchemy-migrate
* First run: ``python dbmanage.py version_control``
* Other runs: ``python dbmanage.py upgrade``

``offtrac.etl``:

* Runs with ``python -mofftrac.etl``
* Requires SQLAlchemy, simplejson
* Create a sqlite3 database (``./db/offtrac.db``) from the
  `JSON File Database`_ using a subset of Trac's schema. This will be done
  incrementally by looking at changes in the git repository.

``offtrac.wsgi``:

* Runs with ``python -mofftrac.start``
* Requires SQLAlchemy, simplejson, Flask, Flask-SQLAlchemy
* Starts read-only web UI at 127.0.0.1:5000 for the local sqlite3 database
  created by ``offtrac.etl``

JSON File Database
==================

This is a bunch of JSON files, dumped by simplejson with sorted keys and one
character indent to make the diffs nice (canonical-ish). Note that wiki and
attachments are not currently synchronized.

* ``db/db.json`` - repository metadata, currently the last timestamp synced from
  Trac::
  
      {
       "recent":"2011-04-09T21:16:07"
      }

* ``db/report/{{id}}.json`` - Stored reports in Trac. SQL based::

      {
       "sql":"-- ## 1: Active Tickets ## --\n\n-- \n--  * List all active […]",
       "title":"Active Tickets"
      }

* ``db/ticket/{{id}}.json`` - Ticket data in the form of
    ``[ticket_id, created, changed, props]``::

      [
       1,
       "2006-08-22T01:42:33",
       "2010-11-25T02:22:00",
       {
        "cc":"",
        "changetime":"2010-11-25T02:22:00",
        "component":"unscreened-engineering",
        "description":"We need a script […]",
        "keywords":"",
        "milestone":"Triage Me",
        "owner":"bob",
        "priority":"Medium",
        "reporter":"bob",
        "resolution":"fixed",
        "status":"closed",
        "summary":"Image banner to click SWF script",
        "time":"2006-08-22T01:42:33",
        "type":"task"
       }
      ]

* ``db/changelog/{{ticket_id}}.json`` - The full changelog for a given ticket
  in the form of ``[isotime, author, field, oldvalue, newvalue, permanent]``.
  permanent is used to distinguish changes that are not immutable
  (attachments)::

      [
       [
        "2007-10-26T17:11:07",
        "bob",
        "comment",
        "1",
        "",
        1
       ],
       [
        "2007-10-26T17:11:07",
        "bob",
        "resolution",
        "",
        "duplicate",
        1
       ],
       [
        "2007-10-26T17:11:07",
        "bob",
        "status",
        "new",
        "closed",
        1
       ]
      ]

* ``db/field/{{field}}/{{name}}.json`` - when field is one of ``component``,
  ``version``, ``milestone``. ``name`` is UTF-8 and URL encoded
  with ``urllib.quote_plus``. These have several slightly different
  structures, but the common factor is that the primary key is ``name``
  and it is text.

  Component::

      {
       "description":"Urgent issues that require the attention of a platform engineer.",
       "name":"platform-oncall",
       "owner":"christopher"
      }
  
  Milestone::

      {
       "completed":0,
       "description":"All tickets that need to be triaged by a PM",
       "due":0,
       "name":"Triage Me"
      }

* ``db/field/{{enum}}/{{name}}.json`` - when field is any enum, such as
  ``priority``, ``resolution``, ``severity``, ``type``. The value is simply
  the value of the enum. Name is encoded UTF-8 with quote_plus URL encoding as
  above::
  
      "1"