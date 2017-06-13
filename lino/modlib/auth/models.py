# -*- coding: UTF-8 -*-
# Copyright 2011-2017 Luc Saffre
# License: BSD (see file COPYING for details)
"""Database models for this plugin.

Documentation is in :doc:`/specs/users` and :doc:`/dev/users`

"""

from builtins import str
from builtins import object

from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager

from lino.api import dd, rt, _
from lino.utils.xmlgen.html import E
from lino.core import userprefs
from lino.core.fields import NullCharField
from lino.core.roles import SiteAdmin

from lino.mixins import CreatedModified, Contactable

from .choicelists import UserTypes
from .mixins import UserAuthored, TimezoneHolder
from .actions import ChangePassword, SendWelcomeMail
from .utils import AnonymousUser

class UserManager(BaseUserManager):
    pass

@python_2_unicode_compatible
class User(AbstractBaseUser, Contactable, CreatedModified, TimezoneHolder):
    class Meta(object):
        app_label = 'auth'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        abstract = dd.is_abstract_model(__name__, 'User')
        ordering = ['last_name', 'first_name', 'username']

    USERNAME_FIELD = 'username'
    _anon_user = None
    objects = UserManager()

    # anonymous_user_class = AnonymousUser

    preferred_foreignkey_width = 15
    hidden_columns = 'password remarks'
    authenticated = True

    username = NullCharField(_('Username'), max_length=30, unique=True)
    user_type = UserTypes.field(blank=True)
    initials = models.CharField(_('Initials'), max_length=10, blank=True)
    first_name = models.CharField(_('First name'), max_length=30, blank=True)
    last_name = models.CharField(_('Last name'), max_length=30, blank=True)
    remarks = models.TextField(_("Remarks"), blank=True)  # ,null=True)

    change_password = ChangePassword()

    def __str__(self):
        return self.get_full_name()

    def get_as_user(self):
        """Overrides
        :meth:`lino_xl.lib.contacts.models.Partner.get_as_user`.

        """
        return self
    
    def get_full_name(self):
        if not self.first_name and not self.last_name:
            return self.initials or self.username
        return u'{} {}'.format(self.first_name, self.last_name).strip()

    @dd.displayfield(_("Name"), max_length=15)
    def name_column(self, request):
        # return join_words(self.last_name.upper(),self.first_name)
        return str(self)

    def get_person(self):
        if self.partner:
            return self.partner.get_mti_child('person')

    person = property(get_person)

    def is_editable_by_all(self):
        return False
    
    def get_row_permission(self, ar, state, ba):
        #~ print 20120621, self, user, state, action
        # import pdb ; pdb.set_trace()
        if not ba.action.readonly:
            user = ar.get_user()
            if user != self:
                if not user.user_type.has_required_roles([SiteAdmin]):
                    if not self.is_editable_by_all():
                        return False
        return super(User, self).get_row_permission(ar, state, ba)
        #~ return False

    def disabled_fields(self, ar):
        """
        Only System admins may change the `user_type` of users.
        See also :meth:`Users.get_row_permission`.
        """
        rv = super(User, self).disabled_fields(ar)
        if not ar.get_user().user_type.has_required_roles([SiteAdmin]):
            rv.add('user_type')
        return rv

    def full_clean(self, *args, **kw):
        p = self.get_person()
        if p is not None and p != self:
            for n in ('first_name', 'last_name', 'email', 'language'):
                if not getattr(self, n):
                    setattr(self, n, getattr(p, n))
            #~ self.language = p.language
        if not self.language:
            #~ self.language = settings.SITE.DEFAULT_LANGUAGE.django_code
            self.language = settings.SITE.get_default_language()
        if not self.password:
            self.set_unusable_password()
        # if not self.initials:
        #     if self.first_name and self.last_name:
        #         self.initials = self.first_name[0] + self.last_name[0]
        super(User, self).full_clean(*args, **kw)

    def get_received_mandates(self):
        #~ return [ [u.id,_("as %s")%u] for u in self.__class__.objects.all()]
        return [[u.id, str(u)] for u in self.__class__.objects.all()]
        #~ return self.__class__.objects.all()

    # @dd.htmlbox(_("Welcome"))
    # def welcome_email_body(self, ar):
    #     # return join_words(self.last_name.upper(),self.first_name)
    #     return self.get_welcome_email_body(ar)

    def get_welcome_email_body(self, ar):
        template = rt.get_template('users/welcome_email.eml')
        context = self.get_printable_context(ar)
        # dict(obj=self, E=E, rt=rt)
        return template.render(**context)
        
    def as_list_item(self, ar):
        if settings.SITE.is_demo_site:
            p = "'{0}', '{1}'".format(self.username, '1234')
        else:
            p = "'{0}'".format(self.username)
        url = "javascript:Lino.show_login_window(null, {0})".format(p)
        return E.li(E.a(self.username, href=url), ' : ',
                    str(self), ', ',
                    str(self.user_type), ', ',
                    E.strong(settings.SITE.LANGUAGE_DICT.get(self.language)))

    @classmethod
    def get_by_username(cls, username, default=models.NOT_PROVIDED):
        """
        `User.get_by_username(x)` is equivalent to
        `User.objects.get(username=x)` except that the text
        of the DoesNotExist exception is more useful.
        """
        try:
            return cls.objects.get(username=username)
        except cls.DoesNotExist:
            if default is models.NOT_PROVIDED:
                raise cls.DoesNotExist(
                    "No %s with username %r" % (
                        str(cls._meta.verbose_name), username))
            return default

    def get_preferences(self):
        """Return the preferences of this user. The returned object is a
        :class:`lino.core.userprefs.UserPrefs` object.

        """
        return userprefs.reg.get(self)
    
    @classmethod
    def get_anonymous_user(cls):
        return AnonymousUser()
        # if cls._anon_user is None:
        #     cls._anon_user = AnonymousUser()
        # return cls._anon_user
    
    # @dd.action(label=_("Send e-mail"),
    #            show_in_bbar=True, show_in_workflow=False,
    #            button_text="✉")  # u"\u2709"
    # def do_send_email(self, ar):
    #     self.send_welcome_email()

    # send_email = SendWelcomeMail()

class Authority(UserAuthored):
    class Meta(object):
        app_label = 'auth'
        verbose_name = _("Authority")
        verbose_name_plural = _("Authorities")


    authorized = models.ForeignKey(settings.SITE.user_model)

    @dd.chooser()
    def authorized_choices(cls, user):
        qs = settings.SITE.user_model.objects.exclude(
            user_type=None)
            #~ user_type=UserTypes.blank_item) 20120829
        if user is not None:
            qs = qs.exclude(id=user.id)
            #~ .exclude(level__gte=UserLevels.admin)
        return qs

@dd.receiver(dd.pre_startup)
def inject_partner_field(sender=None, **kwargs):

    User = sender.models.auth.User

    if dd.is_installed('contacts'):
        Partner = sender.models.contacts.Partner
        if not issubclass(User, Partner):
            dd.inject_field(User, 'partner', dd.ForeignKey(
                'contacts.Partner', blank=True, null=True,
                related_name='users_by_partner',
                on_delete=models.PROTECT))
            # a related_name is needed so that Avanti can have aClient
            # who inherits from both Partner and UserAuthored
            return
    dd.inject_field(User, 'partner', dd.DummyField())

    
class Permission(dd.Model):
    class Meta(object):
        app_label = 'auth'
        abstract = True

# from django.contrib.auth.models import Permission
# Permission._meta.app_label = 'auth'