# -*- coding: utf-8 -*-

import re
import sys
import weakref
from xml.parsers.expat import ExpatError
if sys.version_info[0] == 3:
    from xmlrpc.client import ServerProxy, Binary, Fault
    from urllib.parse import urlencode
else:
    from xmlrpclib import ServerProxy, Binary, Fault
    from urllib import urlencode

ERR = 'XML or text declaration not at start of entity: line 2, column 0'

def utc2local(date):
    from datetime import datetime, timedelta
    date_offset = (datetime.now() - datetime.utcnow())
    # Python < 2.7 don't have the 'total_seconds' method so calculate it by hand!
    date_offset = (date_offset.microseconds +
        (date_offset.seconds + date_offset.days * 24 * 3600) * 1e6) / 1e6
    date_offset = int(round(date_offset / 60 / 60))
    return date + timedelta(hours=date_offset)


class DokuWikiError(Exception):
    pass


class DokuWiki(object):
    def __init__(self, url, user, password, **kwargs):
        """Initialize the object by connecting to the XMLRPC server."""
        # Initialize XMLRPC client.
        url = '%s/lib/exe/xmlrpc.php?%s' % (
            url, urlencode({'u': user, 'p': password}))
        self.proxy = ServerProxy(url, **kwargs)

        # Set "namespaces" for pages and medias functions.
        self.pages = _Pages(weakref.ref(self)())
        self.medias = _Medias(weakref.ref(self)())

    def send(self, command, *args, **kwargs):
        """Method for executing XMLRPC command and catching exception."""
        args = list(args)
        if kwargs:
            args.append(kwargs)

        method = self.proxy
        for elt in command.split('.'):
            method = getattr(method, elt)

        try:
            return method(*args)
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
    def version(self):
        """Return the Dokuwiki version."""
        return self.send('dokuwiki.getVersion')

    @property
    def time(self):
        return self.send('dokuwiki.getTime')

    @property
    def xmlrpc_version(self):
        return self.send('dokuwiki.getXMLRPCAPIVersion')

    @property
    def xmlrpc_supported_version(self):
        return self.send('wiki.getRPCVersionSupported')

    @property
    def title(self):
        return self.send('dokuwiki.getTitle')

    def login(self, user, password):
        return self.send('dokuwiki.login', user, password)

    def add_acl(self, scope, user, permission):
        return self.send('plugin.acl.addAcl', scope, user, permission)

    def del_acl(self, scope, user, permission):
        return self.send('plugin.acl.delAcl', scope, user)


class _Pages(object):
    def __init__(self, dokuwiki):
        self._dokuwiki = dokuwiki

    def list(self, namespace='/', **options):
        return self._dokuwiki.send('dokuwiki.getPagelist', namespace, **options)

    def changes(self, timestamp):
        return self._dokuwiki.send('wiki.getRecentChanges', timestamp)

    def search(self, string):
        return self._dokuwiki.send('dokuwiki.search', string)

    def versions(self, pagename, offset=0):
        return self._dokuwiki.send('wiki.getPageVersions', pagename, offset)

    def info(self, pagename, version=''):
        return (self._dokuwiki.send('wiki.getPageInfoVersion', pagename, version)
            if version else self._dokuwiki.send('wiki.getPageInfo', pagename))

    def get(self, pagename, version=''):
        return (self._dokuwiki.send('wiki.getPageVersion', pagename, version))

    def append(self, pagename, content, **options):
        return self._dokuwiki.send(
            'dokuwiki.appendPage', pagename, content, **options)

    def html(self, pagename, version=''):
        return (self._dokuwiki.send('wiki.getPageHTMLVersion', pagename, version)
            if version else self._dokuwiki.send('wiki.getPageHTML', pagename))

    def set(self, pagename, content, **options):
        try:
            return self._dokuwiki.send(
                'wiki.putPage', pagename, content, **options)
        except ExpatError as err:
            # Sometime the first line of the XML response is blank which raise
            # the 'ExpatError' exception although the change has been done. This
            # allow to ignore the error.
            if str(err) != ERR:
                raise DokuWikiError(err)

    def delete(self, pagename):
        return self.set(pagename, '')

    def lock(self, pagename):
        result = self._dokuwiki.send(
            'dokuwiki.setLocks', lock=[pagename], unlock=[])
        if result['lockfail']:
            raise DokuWikiError('unable to lock page')

    def unlock(self, pagename):
        result = self._dokuwiki.send(
            'dokuwiki.setLocks', lock=[], unlock=[pagename])
        if result['unlockfail']:
            raise DokuWikiError('unable to unlock page')

    def permission(self, pagename):
        return self._dokuwiki.send('wiki.aclCheck', pagename)

    def links(self, pagename):
        return self._dokuwiki.send('wiki.listLinks', pagename)

    def backlinks(self, pagename):
        return self._dokuwiki.send('wiki.getBackLinks', pagename)


class _Medias(object):
    def __init__(self, dokuwiki):
        self._dokuwiki = dokuwiki

    def changes(self, timestamp):
        return self._dokuwiki.send('wiki.getRecentMediaChanges', timestamp)

    def list(self, namespace='/', **options):
        return self._dokuwiki.send('wiki.getAttachments', namespace, **options)

    def get(self, media, dirpath, filename='', overwrite=False):
        import os
        if not filename:
            filename = media.replace('/', ':').split(':')[-1]
        if not os.path.exists(dirpath):
            os.makedirs(dirpath)
        filepath = os.path.join(dirpath, filename)
        if os.path.exists(filepath) and not overwrite:
            raise FileExistsError("[Errno 17] File exists: '%s'" % filepath)
        with open(filepath, 'wb') as fhandler:
            fhandler.write(self._dokuwiki.send('wiki.getAttachment', media).data)

    def info(self, media):
        return self._dokuwiki.send('wiki.getAttachmentInfo', media)

    def add(self, media, filepath, overwrite=True):
        with open(filepath, 'rb') as fhandler:
            self._dokuwiki.send('wiki.putAttachment',
                media, Binary(fhandler.read()), ow=overwrite)

    def delete(self, media):
        return self._dokuwiki.send('wiki.deleteAttachment', media)


class Dataentry(object):
    @staticmethod
    def get(content, keep_order=False):
        if keep_order:
            from collections import OrderedDict
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
            dataentry.setdefault(line_split[0].strip(),
                re.sub('#.*$', '', ':'.join(line_split[1:])).strip())

        if not found:
            raise DokuWikiError('no dataentry found')
        return dataentry

    @staticmethod
    def gen(name, datas):
        return '---- dataentry %s ----\n%s\n----' % (name, '\n'.join(
            '%s:%s' % (attr, value) for attr, value in datas.items()))

    @staticmethod
    def ignore(content):
        page_content = []
        start = False
        for line in content.split('\n'):
            if line == '----' and not start:
                start = True
                continue
            if start:
                page_content.append(line)
        return '\n'.join(page_content) if page_content else content
