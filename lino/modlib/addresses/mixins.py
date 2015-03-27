# Copyright 2014-2015 Luc Saffre
# License: BSD (see file COPYING for details)

"""
Model mixins for `lino.modlib.addresses`.

"""

from __future__ import unicode_literals
from __future__ import print_function

from django.utils.translation import ugettext_lazy as _

from lino.api import rt, dd
from lino.utils.xmlgen.html import E
from lino.core.utils import ChangeWatcher

from .choicelists import AddressTypes


class AddressOwner(dd.Model):
    """Base class for the "addressee" of any address.

    """
    class Meta:
        abstract = True

    def get_address_by_type(self, address_type):
        Address = rt.modules.addresses.Address
        try:
            return Address.objects.get(
                partner=self, address_type=address_type)
        except Address.DoesNotExist:
            return self.get_primary_address()
        except Address.MultipleObjectsReturned:
            return self.get_primary_address()

    def get_primary_address(self):
        """Return the primary address of this partner.

        """
        Address = rt.modules.addresses.Address
        try:
            return Address.objects.get(partner=self, primary=True)
        except Address.DoesNotExist:
            pass

    def sync_primary_address(self, request):
        Address = rt.modules.addresses.Address
        watcher = ChangeWatcher(self)
        kw = dict(partner=self, primary=True)
        try:
            pa = Address.objects.get(**kw)
            for k in Address.ADDRESS_FIELDS:
                setattr(self, k, getattr(pa, k))
        except Address.DoesNotExist:
            pa = None
            for k in Address.ADDRESS_FIELDS:
                fld = self._meta.get_field(k)
                setattr(self, k, fld.get_default())
        self.save()
        watcher.send_update(request)

    def get_overview_elems(self, ar):
        elems = super(AddressOwner, self).get_overview_elems(ar)
        sar = ar.spawn('addresses.AddressesByPartner',
                       master_instance=self)
        # btn = sar.as_button(_("Manage addresses"), icon_name="wrench")
        btn = sar.as_button(_("Manage addresses"))
        # elems.append(E.p(btn, align="right"))
        elems.append(E.p(btn))
        return elems
    
from lino.modlib.plausibility.choicelists import Checker


class AddressOwnerChecker(Checker):
    """Checks for the following plausibility problems:

    - :message:`Unique address is not marked primary.` --
      if there is exactly one :class:`Address` object which just fails to
      be marked as primary, mark it as primary and return it.

    - :message:`Non-empty address fields, but no address record.`
      -- if there is no :class:`Address` object, and if the
      :class:`Partner` has some non-empty address field, create an
      address record from these, using `AddressTypes.official` as
      type.

    """
    verbose_name = _("Check for missing or non-primary address records")
    model = AddressOwner
    
    def get_plausibility_problems(self, obj, fix=False):
        Address = rt.modules.addresses.Address
        qs = Address.objects.filter(partner=obj)
        num = qs.count()
        if num == 0:
            kw = dict()
            for fldname in Address.ADDRESS_FIELDS:
                v = getattr(obj, fldname)
                if v:
                    kw[fldname] = v
            if kw:
                yield (True,
                       _("Owner with address, but no address record."))
                if fix:
                    kw.update(partner=obj, primary=True)
                    kw.update(address_type=AddressTypes.official)
                    addr = Address(**kw)
                    addr.full_clean()
                    addr.save()
        elif num == 1:
            addr = qs[0]
            # check whether it is the same address than the one
            # specified on AddressOwner
            diffs = {}
            for k in Address.ADDRESS_FIELDS:
                my = getattr(addr, k)
                other = getattr(obj, k)
                if my != other:
                    diffs[k] = (my, other)
            if addr.primary and not diffs:
                return  # that's the normal case. no problem.
            if not addr.primary:
                yield (True, _("Unique address is not marked primary."))
                if fix:
                    addr.primary = True
            if addr.primary and len(diffs):
                msg = _("Primary address differs from owner address ({0}).")
                diffstext = [
                    _("{0}:{1}->{2}").format(k, *v) for k, v in diffs.items()]
                msg = msg.format(', '.join(diffstext))
                yield (True, msg)
                if fix:
                    for k, v in diffs.items():
                        (my, other) = v
                        setattr(addr, k, other)
            if fix:
                addr.full_clean()
                addr.save()
        else:
            qs = qs.filter(primary=True)
            num = qs.count()
            if num == 0:
                yield (False, _("Multiple addresses, but none is primary."))
            elif num != 1:
                yield (False, _("Multiple primary addresses."))

AddressOwnerChecker.activate()
