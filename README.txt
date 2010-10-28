Screwing around with trac RPC
https://trac.mochimedia.net/login/rpc

Reports (in SQL anyway) can be done like this:
https://trac.mochimedia.net/report?asc=1&format=tab (report list)
https://trac.mochimedia.net/report?id=22&format=sql (report SQL)

but SQL reports are deprecated so maybe we should look at TracQuery
instead? Some of our ordering stuff can't be done directly in
this syntax, so maybe we punt on this for now.
https://trac.mochimedia.net/query
https://trac.mochimedia.net/wiki/TracQuery

DB schema:
http://trac.edgewall.org/wiki/TracDev/DatabaseSchema
