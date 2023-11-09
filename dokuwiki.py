# -*- coding: utf-8 -*-

"""This python module aims to manage
`DokuWiki <https://www.dokuwiki.org/dokuwiki>`_ wikis by using the
provided `XML-RPC API <https://www.dokuwiki.org/devel:xmlrpc>`_.  It is
compatible with python3+.

Installation
------------
It is on `PyPi <https://pypi.python.org/pypi/dokuwiki>`_ so you can use
the ``pip`` command to install it::

    pip install dokuwiki

Otherwise sources are in `github <https://github.com/fmenabe/python-dokuwiki>`_
"""

import base64
import re
import weakref
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from typing import OrderedDict as t_OrderedDict
from urllib.parse import quote
from xml.parsers.expat import ExpatError
from xmlrpc.client import ServerProxy, Binary, Fault, Transport, SafeTransport, ProtocolError, DateTime

if TYPE_CHECKING:
    import http.client

ERR = 'XML or text declaration not at start of entity: line 2, column 0'

_URL_RE = re.compile(r'(?P<proto>https?)://(?P<host>[^/]*)(?P<uri>/.*)?')

def date(dte: DateTime ) -> datetime:
    """DokuWiki returns dates of `xmlrpc.client` ``DateTime``
    type and the format changes between DokuWiki versions ... This function
    convert *date* to a `datetime` object.
    """
    date = dte.value
    return (datetime.strptime(date[:-5], '%Y-%m-%dT%H:%M:%S')
            if len(date) == 24
            else datetime.strptime(date, '%Y%m%dT%H:%M:%S'))

def utc2local(date: datetime) -> datetime:
    """DokuWiki returns date with a +0000 timezone. This function convert *date*
    to the local time.
    """
    date_offset = (datetime.now() - datetime.utcnow()).total_seconds()
    date_offset = int(round(date_offset / 60 / 60))
    return date + timedelta(hours=date_offset)


class DokuWikiError(Exception):
    """Exception raised by this module when there is an error."""
    pass


def CookiesTransport(proto: str = 'https') -> Transport:
    """Generate transport class when using cookie based authentication."""
    _TransportClass_ = Transport if proto == 'http' else SafeTransport

    class CookiesTransport(_TransportClass_):
        """A Python3 xmlrpc.client.Transport subclass that retains cookies."""
        def __init__(self) -> None:
            super().__init__(self)
            self._cookies: Dict[str, str] = dict()

        def send_headers(
            self,
            connection: http.client.HTTPConnection,
            headers: Dict[str, str]
        ) -> None:
            if self._cookies:
                cookies = map(lambda x: x[0] + '=' + x[1], self._cookies.items())
                connection.putheader('Cookie', '; '.join(cookies))
            super().send_headers(self, connection, headers)

        def parse_response(
            self,
            response: http.client.HTTPResponse
        ) -> Any:
            """parse and store cookie"""
            try:
                set_cookie = response.msg.get_all("Set-Cookie")
                assert set_cookie is not None
                for header in set_cookie:
                    cookie = header.split(";", 1)[0]
                    cookieKey, cookieValue = cookie.split("=", 1)
                    self._cookies[cookieKey] = cookieValue
            finally:
                return super().parse_response(self, response)

    return CookiesTransport()


class DokuWiki:
    """Initialize a connection to a DokuWiki wiki. ``url``, ``user`` and
    ``password`` are respectively the URL, the login and the password for
    connecting to the wiki. ``kwargs`` are `xmlrpc.client`
    **ServerProxy** parameters.

    The exception `DokuWikiError` is raised if the authentication
    fails but others exceptions (like `socket.gaierror` for invalid domain,
    `xmlrpc.client.ProtocolError` for an invalid wiki, ...) are not catched.

    .. code::

        try:
            wiki = dokuwiki.DokuWiki('URL', 'USER', 'PASSWORD')
        except (DokuWikiError, Exception) as err:
            print('unable to connect: %s' % err)

    .. note::

        The URL format is: ``PROTO://FQDN[/PATH]`` (*https://www.example.com/dokuwiki*
        for example).

    To use cookie based authentication (use HTTP cookies instead of passing login
    and password in the URI), set ``cookieAuth`` parameter to *True*:

    .. code::

        wiki = dokuwiki.DokuWiki('URL', 'USER', 'PASSWORD', cookieAuth=True)
    """
    def __init__(self, url: str, user:str, password: str, **kwargs: Any) -> None:
        """Initialize the object by connecting to the XMLRPC server."""
        # Parse input URL
        search = _URL_RE.search(url)
        if search is None:
            raise DokuWikiError("invalid url '%s'" %  url)
        params = search.groupdict()

        # Set auth string or transport for cookie based authentication.
        auth = '{:s}:{:s}@'.format(user, quote(password, safe=''))
        cookie_auth = kwargs.pop('cookieAuth', False)
        if cookie_auth:
            auth = ''
            kwargs['transport'] = CookiesTransport(params['proto'])

        xmlrpc_url = '%s://%s%s%s/lib/exe/xmlrpc.php' % (
            params['proto'], auth, params['host'], params['uri'] or '')
        self.proxy = ServerProxy(xmlrpc_url, **kwargs)

        # Force login for cookie based authentication.
        if cookie_auth and not self.login(user, password):
            raise DokuWikiError('invalid login or password!')

        # Dummy call to ensure the connection is up.
        try:
            self.version
        except ProtocolError as err:
            if err.errcode == 401:
                raise DokuWikiError('invalid login or password!')
            raise

        # Set "namespaces" for pages and medias functions.
        self.pages = _Pages(weakref.ref(self)())
        self.medias = _Medias(weakref.ref(self)())
        self.structs = _Structs(weakref.ref(self)())

    def send(self, command: str, *args: Any, **kwargs: Any) -> Any:
        """Generic method for executing an XML-RPC *command*. *args* and
        *kwargs* are the arguments and parameters needed by the command.
        """
        argsl = list(args)
        if kwargs:
            argsl.append(kwargs)

        method = self.proxy
        for elt in command.split('.'):
            method = getattr(method, elt)

        try:
            return method(*argsl)
        except Fault as err:
            if err.faultCode == 121:
                return {}
            elif err.faultCode == 321:
                return []
            raise DokuWikiError(err)
        except ExpatError as err:
            if str(err) != ERR:
                raise DokuWikiError(err)

    @property
    def version(self) -> str:
        """Property that returns the DokuWiki version of the remote Wiki."""
        version = self.send('dokuwiki.getVersion')
        assert type(version) is str
        return version

    @property
    def time(self) -> int:
        """Property that returns the current time at the remote wiki server as
        Unix timestamp.
        """
        return self.send('dokuwiki.getTime')

    @property
    def xmlrpc_version(self) -> str:
        """Property that returns the XML RPC interface version of the remote
        Wiki. This is DokuWiki implementation specific and independent of the
        supported standard API version returned by ``wiki.getRPCVersionSupported``.
        """
        version = self.send('dokuwiki.getXMLRPCAPIVersion')
        assert type(version) is str
        return version

    @property
    def xmlrpc_supported_version(self) -> str:
        """Property that returns *2* with the supported RPC API version."""
        return self.send('wiki.getRPCVersionSupported')

    @property
    def title(self) -> str:
        """Property that returns the title of the wiki."""
        title = self.send('dokuwiki.getTitle')
        assert type(title) is str
        return title

    def login(self, user: str, password: str) -> bool:
        """Log to the wiki using *user* and *password* credentials. It returns
        a boolean that indicates if the user succesfully authenticate."""
        return self.send('dokuwiki.login', user, password)

    def add_acl(self, scope: str, user: str, permission: str) -> bool:
        """Add an `ACL <https://www.dokuwiki.org/acl>`_ rule that restricts
        the page/namespace *scope* to *user* (use *@group* syntax for groups)
        with *permission* level. It returns a boolean that indicate if the rule
        was correctly added.
        """
        return self.send('plugin.acl.addAcl', scope, user, permission)

    def del_acl(self, scope: str, user: str):
        """Delete any ACL matching the given *scope* and *user* (or group if
        *@group* syntax is used). It returns a boolean that indicate if the rule
        was correctly removed.
        """
        return self.send('plugin.acl.delAcl', scope, user)


class _Pages:
    """This object regroup methods for managing pages of a DokuWiki. This object
    is accessible from the ``pages`` property of an `DokuWiki` instance::

        wiki = dokuwiki.DokuWiki('URL', 'User', 'Password')
        wiki.pages.list()
    """

    def __init__(self, dokuwiki: DokuWiki) -> None:
        self._dokuwiki = dokuwiki

    def list(self, namespace: str='/', **options: Dict[str, Any]) -> List[str]:
        """List all pages of the given *namespace*.

        Valid *options* are:

            * *depth*: (int) recursion level, 0 for all
            * *hash*: (bool) do an md5 sum of content
            * *skipacl*: (bool) list everything regardless of ACL
        """
        pages = self._dokuwiki.send('dokuwiki.getPagelist', namespace, options)
        assert type(pages) is list
        return pages

    def changes(self, timestamp: str) -> List[str]:
        """Returns a list of changes since given *timestamp*.

        For example, for returning all changes since *2016-01-01*::

            from datetime import datetime
            wiki.pages.changes(datetime(2016, 1, 1).timestamp())
        """
        changes = self._dokuwiki.send('wiki.getRecentChanges', timestamp)
        assert type(changes) is list
        return changes

    def search(self, string: str) -> List[str]:
        """Performs a fulltext search on *string* and returns the first 15
        results.
        """
        return self._dokuwiki.send('dokuwiki.search', string)

    def versions(self, page: str, offset: int = 0) -> List[str]:
        """Returns the available versions of *page*. *offset* can be used to
        list earlier versions in the history.
        """
        return self._dokuwiki.send('wiki.getPageVersions', page, offset)

    def info(self, page: str, version: Optional[str] = None):
        """Returns informations of *page*. Informations of the last version
        is returned if *version* is not set.
        """
        return (self._dokuwiki.send('wiki.getPageInfoVersion', page, version)
                if version is not None
                else self._dokuwiki.send('wiki.getPageInfo', page))

    def get(self, page: str, version: Optional[str] = None) -> str:
        """Returns the content of *page*. The content of the last version is
        returned if *version* is not set.
        """
        return (self._dokuwiki.send('wiki.getPageVersion', page, version)
                if version is not None
                else self._dokuwiki.send('wiki.getPage', page))


    def append(self, page: str, content: str, **options: Dict[str, Any]):
        """Appends *content* text to *page*.

        Valid *options* are:

            * *sum*: (str) change summary
            * *minor*: (bool) whether this is a minor change
        """
        return self._dokuwiki.send('dokuwiki.appendPage', page, content, options)

    def html(self, page: str, version: Optional[str] = None) -> str:
        """Returns HTML content of *page*. The HTML content of the last version
        of the page is returned if *version* is not set.
        """
        return (self._dokuwiki.send('wiki.getPageHTMLVersion', page, version)
                if version is not None
                else self._dokuwiki.send('wiki.getPageHTML', page))

    def set(self, page: str, content: str, **options: Dict[str, Any]):
        """Set/replace the *content* of *page*.

        Valid *options* are:

            * *sum*: (str) change summary
            * *minor*: (bool) whether this is a minor change
        """
        try:
            return self._dokuwiki.send('wiki.putPage', page, content, options)
        except ExpatError as err:
            # Sometime the first line of the XML response is blank which raise
            # the 'ExpatError' exception although the change has been done. This
            # allow to ignore the error.
            if str(err) != ERR:
                raise DokuWikiError(err)

    def delete(self, page: str):
        """Delete *page* by setting an empty content."""
        return self.set(page, '')

    def lock(self, page: str) -> None:
        """Locks *page*."""
        result = self._dokuwiki.send('dokuwiki.setLocks',
                                     lock=[page], unlock=[])
        if result['lockfail']:
            raise DokuWikiError('unable to lock page')

    def unlock(self, page: str) -> None:
        """Unlocks *page*."""
        result = self._dokuwiki.send('dokuwiki.setLocks',
                                     lock=[], unlock=[page])
        if result['unlockfail']:
            raise DokuWikiError('unable to unlock page')

    def permission(self, page: str):
        """Returns the permission level of *page*."""
        return self._dokuwiki.send('wiki.aclCheck', page)

    def links(self, page: str) -> List[str]:
        """Returns a list of all links contained in *page*."""
        return self._dokuwiki.send('wiki.listLinks', page)

    def backlinks(self, page: str):
        """Returns a list of all links referencing *page*."""
        return self._dokuwiki.send('wiki.getBackLinks', page)


class _Medias:
    """This object regroup methods for managing medias of a DokuWiki. This
    object is accessible from the ``medias`` property of an `DokuWiki`
    instance::

        wiki = dokuwiki.DokuWiki('URL', 'User', 'Password')
        wiki.medias.list()
    """
    def __init__(self, dokuwiki: DokuWiki) -> None:
        self._dokuwiki = dokuwiki

    def list(self, namespace: str='/', **options: Dict[str, Any]):
        """Returns all medias of the given *namespace*.

        Valid *options* are:

            * *depth*: (int) recursion level, 0 for all
            * *skipacl*: (bool) skip acl checking
            * *pattern*: (str) check given pattern
            * *hash*: (bool) add hashes to result list
        """
        return self._dokuwiki.send('wiki.getAttachments', namespace, options)

    def changes(self, timestamp: str):
        """Returns the list of medias changed since given *timestamp*.

        For example, for returning all changes since *2016-01-01*::

            from datetime import datetime
            wiki.medias.changes(datetime(2016, 1, 1).timestamp())
        """
        return self._dokuwiki.send('wiki.getRecentMediaChanges', timestamp)

    def get(
        self,
        media: str,
        dirpath: Optional[str] = None,
        filename: Optional[str] = None,
        overwrite: bool = False,
        b64decode: bool = False
    ) -> Optional[bytes]:
        """Returns the binary data of *media* or save it to a file. If *dirpath*
        is not set the binary data is returned, otherwise the data is saved
        to a file. By default, the filename is the name of the media but it can
        be changed with *filename* parameter. *overwrite* parameter allow to
        overwrite the file if it already exists locally.
        """
        import os
        data = self._dokuwiki.send('wiki.getAttachment', media)
        data = base64.b64decode(data) if b64decode else data.data
        if dirpath is None:
            return data

        if filename is None:
            filename = media.replace('/', ':').split(':')[-1]
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filepath = os.path.join(dirpath, filename)
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError("[Errno 17] File exists: '%s'" % filepath)

        with open(filepath, 'wb') as fhandler:
            fhandler.write(data)
        return None

    def info(self, media: str):
        """Returns informations of *media*."""
        return self._dokuwiki.send('wiki.getAttachmentInfo', media)

    def add(self, media: str, filepath: str, overwrite: bool = True) -> None:
        """Set *media* from local file *filepath*. *overwrite* parameter specify
        if the media must be overwrite if it exists remotely.
        """
        with open(filepath, 'rb') as fhandler:
            self._dokuwiki.send('wiki.putAttachment', media,
                                Binary(fhandler.read()), ow=overwrite)

    def set(
        self,
        media: str,
        _bytes: bytes,
        overwrite: bool = True,
        b64encode: bool = False
    ) -> None:
        """Set *media* from *_bytes*. *overwrite* parameter specify if the media
        must be overwrite if it exists remotely.
        """
        data = base64.b64encode(_bytes) if b64encode else Binary(_bytes)
        self._dokuwiki.send('wiki.putAttachment', media, data, ow=overwrite)

    def delete(self, media: str):
        """Delete *media*."""
        return self._dokuwiki.send('wiki.deleteAttachment', media)


class _Structs:
    def __init__(self, dokuwiki: DokuWiki) -> None:
        """Get the structured data of a given page."""
        self._dokuwiki = dokuwiki

    def get_data(self, page: str, schema: str = '', timestamp: int = 0):
        """Get the structured data of a given page."""
        return self._dokuwiki.send('plugin.struct.getData', page, schema, timestamp)

    def save_data(self, page: str, data: str, summary: str='', minor: bool = False):
        """Saves data for a given page (creates a new revision)."""
        return self._dokuwiki.send('plugin.struct.saveData', page, data, summary, minor)

    def get_schema(self, name: str=''):
        """Get info about existing schemas columns."""
        return self._dokuwiki.send('plugin.struct.getSchema', name)

    def get_aggregation_data(
        self,
        schemas: List[str],
        columns: List[str],
        data_filter: List[str] = [],
        sort: str=''
    ):
        """Get the data that would be shown in an aggregation."""
        return self._dokuwiki.send(
            'plugin.struct.getAggregationData', schemas, columns, data_filter, sort)


class Dataentry:
    """Object that manage `data entries <https://www.dokuwiki.org/plugin:data>`_."""

    @staticmethod
    def get(content: str, keep_order: bool = False) -> Union[Dict[str, str], t_OrderedDict[str, str]]:
        """Get dataentry from *content*. *keep_order* indicates whether to
        return an ordered dictionary."""
        dataentry: Union[Dict[str, str], t_OrderedDict[str, str]]
        if keep_order:
            dataentry = OrderedDict()
        else:
            dataentry = {}

        found = False
        for line in content.split('\n'):
            if line.strip().startswith('---- dataentry'):
                found = True
                continue
            elif line == '----':
                break
            elif not found:
                continue

            line_split = line.split(':')
            key = line_split[0].strip()
            value = re.sub('#.*$', '', ':'.join(line_split[1:])).strip()
            dataentry.setdefault(key, value)

        if not found:
            raise DokuWikiError('no dataentry found')
        return dataentry

    @staticmethod
    def gen(name: str, data: Dict[str, str]) -> str:
        """Generate dataentry *name* from *data*."""
        return '---- dataentry %s ----\n%s\n----' % (name, '\n'.join(
            '%s:%s' % (attr, value) for attr, value in data.items()))

    @staticmethod
    def ignore(content: str) -> str:
        """Remove dataentry from *content*."""
        page_content = []
        start = False
        for line in content.split('\n'):
            if line == '----' and not start:
                start = True
                continue
            if start:
                page_content.append(line)
        return '\n'.join(page_content) if page_content else content
