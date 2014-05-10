# -*- coding: UTF-8 -*-
# Copyright 2002-2014 Luc Saffre
# This file is part of the Lino project.
# Lino is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# Lino is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License
# along with Lino; if not, see <http://www.gnu.org/licenses/>.

"""
The ``lino`` module can be imported even from a Django :xfile:`settings.py` 
file since it does not import any django module.

"""

from __future__ import unicode_literals

import os

from os.path import join, abspath, dirname, normpath, isdir

execfile(join(dirname(__file__), 'project_info.py'))
__version__ = SETUP_INFO['version']
intersphinx_url = "http://docs.lino-framework.org"
srcref_url = 'https://github.com/lsaffre/lino/blob/master/%s'


if False:
    """
    subprocess.Popen() took very long and even got stuck on Windows XP.
    I didn't yet explore this phenomen more.
    """
    # Copied from Sphinx <http://sphinx.pocoo.org>
    from os import path
    package_dir = path.abspath(path.dirname(__file__))
    if '+' in SETUP_INFO['version'] or 'pre' in SETUP_INFO['version']:
        # try to find out the changeset hash if checked out from hg, and append
        # it to __version__ (since we use this value from setup.py, it gets
        # automatically propagated to an installed copy as well)
        try:
            import subprocess
            p = subprocess.Popen(['hg', 'id', '-i', '-R',
                                  path.join(package_dir, '..', '..')],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            if out:
                __version__ += ' (Hg ' + out.strip() + ')'
            #~ if err:
                #~ print err
        except Exception:
            pass


def setup_project(settings_module):
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module
    from django.conf import settings
    from lino.runtime import settings


from .lino_site import Site

from django.utils.translation import ugettext_lazy as _
   
