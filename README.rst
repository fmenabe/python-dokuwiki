python-dokuwiki
===============

Overview
--------
This module has for purpose to manager DokuWiki by using the XML-RPC API.
Details of the API are available at https://www.dokuwiki.org/devel:xmlrpc. The
module is compatible with both python 2 and 3.

Installation
------------
Module is on **PyPi**, so ``pip install dokuwiki`` is enough.

Otherwise sources are on github: https://github.com/fmenabe/python-dokuwiki.

API
---
Functions for manipulate pages and medias are separate in two objects accessible
via the 'pages' and 'medias' attributes of the **DokuWiki** object.

utc2local(date)
~~~~~~~~~~~~~~~
Dates returned by some commands are in UTC format. This function convert this
date to the local time.

Dokuwiki.send(command, \*args, \*\*kwargs)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send a **command** to the XML-RPC server (by example: ``dokuwiki.getVersion``).
**\*args** and **\*\*kwargs** are both arguments and options of the command pass
in the request.

Dokuwiki.version
~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.getVersion``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikigetversion).

Dokuwiki.time
~~~~~~~~~~~~~
Send the command ``dokuwiki.getTime`` (
https://www.dokuwiki.org/devel:xmlrpc#dokuwikigetversion).

Dokuwiki.xmlrpc_version
~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.getXMLRPCAPIVersion``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikigetxmlrpcapiversion).

Dokuwiki.xmlrpc_supported_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getRPCVersionSupported``
https://www.dokuwiki.org/devel:xmlrpc#wikigetrpcversionsupported).

Dokuwiki.title
~~~~~~~~~~~~~~
Send the command ``dokuwiki.getTitle``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikigettitle).

Dokuwiki.login(user, password)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.login``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikilogin).

Dokuwiki.pages.list(namespace, \*\*options)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.getPagelist``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikigetpagelist).

Dokuwiki.pages.changes(timestamp)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getRecentChanges``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetrecentchanges).

Dokuwiki.pages.search(string)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.search``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikisearch).

Dokuwiki.pages.versions(pagename, offset=0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getPageVersions``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetpageversions).

Dokuwiki.pages.info(pagename, version='')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getPageInfo``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetpageinfo).

Dokuwiki.pages.get(pagename, version='')
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getPage``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetpage) or ``wiki.getPageVersion`` (
https://www.dokuwiki.org/devel:xmlrpc#wikigetpageversion) if **version** is
given.

Dokuwiki.pages.append(pagename, content, \*\*options)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.appendPage``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikiappendpage).

Dokuwiki.pages.html(pagename, version)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getPageHTML``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetpagehtml) or
``wiki.getPageHTMLVersion`` (
https://www.dokuwiki.org/devel:xmlrpc#wikigetpagehtmlversion) if **version** is
given.

Dokuwiki.pages.set(pagename, content, \*\*options)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.putPage``
(https://www.dokuwiki.org/devel:xmlrpc#wikiputpage).

Dokuwiki.pages.delete(pagename)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.putPage`` with an empty content.

Dokuwiki.pages.lock(pagename)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.setLocks``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikisetlocks). This command take two
lists of pages to lock and unlock. This send the command with the first list
having the **pagename** and the second list empty.

Dokuwiki.pages.unlock(pagename)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``dokuwiki.setLocks``
(https://www.dokuwiki.org/devel:xmlrpc#dokuwikisetlocks). This command take two
lists of pages to lock and unlock. This send the command with the first list
empty and the second list having the **pagename**.

Dokuwiki.pages.permission(pagename)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.aclCheck``
(https://www.dokuwiki.org/devel:xmlrpc#wikiaclcheck).

Dokuwiki.pages.links(pagename)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.listLinks``
(https://www.dokuwiki.org/devel:xmlrpc#wikilistlinks).

Dokuwiki.pages.backlinks(pagename)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getBackLinks``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetbacklinks).

Dokuwiki.medias.changes(timestamp)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getRecentMediaChanges``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetrecentmediachanges).

Dokuwiki.medias.list(namespace, \*\*options)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getAttachments``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetattachments).

Dokuwiki.medias.get(media, dirpath, filename='', overwrite=False)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getAttachment``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetattachment). Save the **media** in
**dirpath** directory. If **filename** is given, the file is rename.
**overwrite** parameter indicate if the file must be ovewrite if it already
exists.

Dokuwiki.medias.info(media)
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.getAttachmentInfo``
(https://www.dokuwiki.org/devel:xmlrpc#wikigetattachmentinfo).

Dokuwiki.medias.add(media, filepath, overwrite)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.putAttachment``
(https://www.dokuwiki.org/devel:xmlrpc#wikiputattachment) with **filepath**
encoded in base64 as data. **overwrite** indicate that an existing file will be
overwrite.

Dokuwiki.medias.delete(media)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Send the command ``wiki.deleteAttachment``
(https://www.dokuwiki.org/devel:xmlrpc#wikideleteattachment).

Example
-------
Code: ::

    import sys
    from dokuwiki import DokuWiki, DokuWikiError

    try:
        wiki = DokuWiki('https://mydoku.example.org/pathtodokuwiki', 'myuser', 'mypassword')
    except DokuWikiError as err:
        print(err)
        sys.exit(1)

    print(wiki.version) # => 'Release 2012-10-13 "Adora Belle"'
    print(wiki.pages.list()) # list all pages of the wiki
    print(wiki.pages.list('my:namespace')) # list all pages in the given namespace
    print(wiki.pages.get('my:namespace:page')) # print the content of the page

For this example to function, ensure:
1) pip install dokuwiki has completed without errors
2) Within the target dokuwiki Configuration Manager web interface, under remote, Enable the remote API system. Restrict the remote user from anyone a certain user.


Release notes
-------------
0.1
~~~
    * Implement DokuWiki XML-RPC commands
    * Compatible with both python 2 and 3

0.2
~~~
    * Manage dataentries (this is a plugin for managing metadatas)
