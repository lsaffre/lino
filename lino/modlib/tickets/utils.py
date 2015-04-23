# -*- coding: UTF-8 -*-
# Copyright 2011-2015 Luc Saffre
# License: BSD (see file COPYING for details)

from django.utils.translation import ugettext_lazy as _
from lino.api import dd, rt


class DependencyTypes(dd.ChoiceList):
    verbose_name = _("Dependency type")
add = DependencyTypes.add_item
add('10', _("Duplicate"), 'duplicate')
add('20', _("Callback"), 'callback')
add('30', _("Requires"), 'requires')

    
class TicketStates(dd.Workflow):

    """
    The state of a ticket (new, open, closed, ...)
    """
    #~ label = _("Ticket State")

    # @classmethod
    # def allow_state_active(cls, self, user):
    #     if not self.reported:
    #         return False
    #     return True

    # @classmethod
    # def allow_state_assigned(cls, self, user):
    #     if not self.user:
    #         return False
    #     return True

    # @classmethod
    # def allow_state_fixed(cls, self, user):
    #     if not self.fixed:
    #         return False
    #     return True


add = TicketStates.add_item

# add('10', _("Assigned"), 'assigned',
#     required=dict(states=['', 'active']),
#     action_name=_("Start"),
#     help_text=_("Ticket has been assigned to somebody who is assigned on it."))
add('10', _("New"), 'new')
add('20', _("Active"), 'active')
add('21', _("Sticky"), 'sticky')
add('30', _("Callback"), 'callback',
    # required=dict(states=['new']),
    # action_name=_("Wait for feedback"),
    help_text=_("Waiting for feedback from partner."))
add('40', _("Fixed"), 'fixed',
    # required=dict(states=['active']),
    help_text=_("Has been fixed. Waiting to be tested."))
add('50', _("Tested"), 'tested',
    # required=dict(states=['fixed']),
    help_text=_("Has been fixed and tested."))
add('60', _("Refused"), 'refused',
    # required=dict(states="tested new active callback"),
    help_text=_("It has been decided that we won't fix this ticket."))
# add('70', _("Sleeping"), 'sleeping',
#     help_text=_("Waiting for better times."))
# add('90', _("Cancelled"), 'cancelled',
#     # required=dict(states=['new active waiting']),
#     help_text=_("Has been cancelled for some reason."))

"""Difference between Cancelled and Refused : Canceled means that we
don't want to talk about this ticket anymore.  Refused makes sense for
tickets which had been asked by a partner. In that case we still may
want to report it.

"""

# class TicketStateGroups(dd.Choice):
#     def __init__(self, 
# class TicketStateGroups(dd.ChoiceList):
#     verbose_name = _("Dependency type")
# add = DependencyTypes.add_item
# add('10', _("Duplicate"), 'duplicate')


@dd.receiver(dd.pre_analyze)
def tickets_workflows(sender=None, **kw):
    """
    """
    TicketStates.active.add_transition(states="new callback")
    TicketStates.callback.add_transition(states="active new fixed")
    TicketStates.fixed.add_transition(states="active new callback")
    TicketStates.tested.add_transition(states="active new callback fixed")
    TicketStates.refused.add_transition(states="active new callback")
    # TicketStates.cancelled.add_transition(states="active new callback")
    # TicketStates.new.add_transition(states="active callback fixed tested")
    # TicketStates.sleeping.add_transition(states="active new callback")

    TicketStates.favorite_states = (TicketStates.sticky, )
    TicketStates.work_states = (TicketStates.active, TicketStates.new)
    TicketStates.waiting_states = (
        TicketStates.callback, TicketStates.fixed, TicketStates.tested)

    # not used:
    # TicketStates.idle_states = (
    #     TicketStates.fixed, TicketStates.tested,
    #     TicketStates.callback, TicketStates.refused)

