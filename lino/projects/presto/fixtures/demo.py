# -*- coding: UTF-8 -*-
# Copyright 2014-2015 Luc Saffre
# License: BSD (see file COPYING for details)

from lino.api import rt


def objects():
    # create a primary Address for each Partner
    for obj in rt.modules.contacts.Partner.objects.all():
        obj.get_primary_address(True)
        yield obj

