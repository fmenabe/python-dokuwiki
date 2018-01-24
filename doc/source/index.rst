.. dokuwiki documentation master file, created by
   sphinx-quickstart on Sat Feb  6 14:16:16 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

python-dokuwiki documentation
=============================

.. toctree::
    :maxdepth: 2

.. automodule:: dokuwiki

API
---
Functions
~~~~~~~~~~
.. autofunction:: date
.. autofunction:: utc2local

Exceptions
~~~~~~~~~~
.. autoclass:: DokuWikiError

Main object
~~~~~~~~~~~
.. autoclass:: DokuWiki
    :members: send, version, time, xmlrpc_version, xmlrpc_supported_version,
                    title, login, add_acl, del_acl
    :member-order: bysource

Pages
~~~~~
.. autoclass:: _Pages
    :members: list, changes, search, versions, info, get, append, html, set,
              delete, lock, unlock, permission, links, backlinks
    :member-order: bysource

Medias
~~~~~~
.. autoclass:: _Medias
    :members: changes, list, get, set, info, add, delete
    :member-order: bysource

Structs
~~~~~~~
.. autoclass:: _Structs
    :members: get_data, save_data, get_schema, get_aggregation_data
    :member-order: bysource

Dataentries
~~~~~~~~~~~
.. autoclass:: Dataentry
    :members: get, gen, ignore
    :member-order: bysource
