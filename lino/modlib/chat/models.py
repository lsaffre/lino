# -*- coding: UTF-8 -*-
# Copyright 2011-2020 Rumma & Ko Ltd
# License: BSD (see file COPYING for details)

from lino.modlib.notify.api import send_notification, send_global_chat
from lino.utils.format_date import fds
from lino.modlib.office.roles import OfficeUser
from lino.modlib.users.mixins import UserAuthored, My
from lino.modlib.gfks.mixins import Controllable
from lino.modlib.memo.mixins import Previewable
from lino.mixins import Created, ObservedDateRange
#from lino_noi.lib.groups.models import Group
from lino.core.site import html2text
from lino.core.gfks import gfk2lookup
from lino.api import dd, rt, _
from lino import DJANGO2
from etgen.html import E, tostring
from django.utils import translation
from django.utils import timezone
from django.conf import settings
from django.db import models
from datetime import timedelta
from lxml import etree
from io import StringIO
import json
import logging
logger = logging.getLogger(__name__)


html_parser = etree.HTMLParser()


def groupname(s):
    # Remove any invalid characters from the given string so that it can
    # be used as a Redis group name.
    # "Group name must be a valid unicode string containing only
    # alphanumerics, hyphens, or periods."

    s = s.replace('@', '-')
    return s.encode('ascii', 'ignore')


class ChatMessage(UserAuthored, Created, Previewable):
    class Meta(object):
        app_label = 'chat'
        verbose_name = _("Chat message")
        verbose_name_plural = _("Chat messages")
        ordering = ['created', 'id']

    # message_type = MessageTypes.field(default="change")

    seen = models.DateTimeField(_("seen"), null=True, editable=False)
    sent = models.DateTimeField(_("sent"), null=True, editable=False)
    group = dd.ForeignKey(
        'groups.Group', blank=True, null=True, related_name="messages")
    #body = dd.RichTextField(_("Body"), editable=False, format='html')

    def __str__(self):
        return "{}: {}".format(self.user, self.body)

        # return _("About {0}").format(self.owner)

    # return self.message
    # return _("Notify {0} about change on {1}").format(
    #     self.user, self.owner)

    def send_global_message(self):

        message = {
            "id": self.pk,
            # "subject": str(self.subject),
            "user": self.user,
            "body": html2text(self.body),
            "created": self.created.strftime("%a %d %b %Y %H:%M"),
        }
        logger.info("Sending Message %s:#%s" % (self.user, self.pk))
        send_global_chat(**message)
        self.sent = timezone.now()
        self.save()

    @classmethod
    def markAsSeen(Cls, data):
        msg_ids = data['body']
        oldMsg = Cls.objects.filter(pk__in=msg_ids,seen__isnull=True)
        oldMsg.update(seen=timezone.now())

    @classmethod
    def onRecive(Cls, data):
        args = dict(
            user=data['user'],
            body=data['body']
        )
        newMsg = Cls(**args)
        newMsg.full_clean()
        newMsg.save()
        newMsg.send_global_message()

    @dd.action(_("ChatsMsg"))
    def getChats(self, ar):
        # doto, have work.
        last_ten = ChatMessage.objects.order_by('-created')[:10]
        last_ten_in_ascending_order = reversed(last_ten)
        return ar.success(rows=[(c.user.username, ar.parse_memo(c.body), c.created, c.seen, c.pk, c.user.id) for c in last_ten_in_ascending_order])

@dd.action(_("ChatsGroupChats"))
def getGroupChats(self, ar):
    Group = rt.models.resolve("groups.Group")
    last_ten = Group.objects.all()[:10]
    last_ten_in_ascending_order = reversed(last_ten)
    return ar.success(rows=[(c.name, c.id) for c in last_ten_in_ascending_order])


dd.inject_action(
    'groups.Group',
    getGroupChats=getGroupChats)
