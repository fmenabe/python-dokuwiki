# -*- coding: utf-8 -*-

import setuptools

setuptools.setup(
    name = 'dokuwiki',
    version = '1.3.1',
    author = 'François Ménabé',
    author_email = 'francois.menabe@gmail.com',
    url = 'http://python-dokuwiki.readthedocs.org/en/latest/',
    download_url='https://github.com/fmenabe/python-dokuwiki',
    license='MIT License',
    description = 'Manage DokuWiki via XML-RPC API.',
    long_description=open('README.rst').read(),
    keywords=['xmlrpc', 'dokuwiki'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
    ],
    py_modules = ['dokuwiki'],
)
