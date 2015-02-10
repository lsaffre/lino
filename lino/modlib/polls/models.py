# -*- coding: UTF-8 -*-
# Copyright 2013-2015 Luc Saffre
# License: BSD (see file COPYING for details)
"""Database models for `lino.modlib.polls`.

.. rubric:: Models overview

A :class:`Poll` is a collection of :class:`Questions <Question>` which
we want to ask repeatedly to different people. Each Question has a
*question text* and a :class:`ChoiceSet`, i.e. a stored ordered set of
possible choices.  A :class:`Response` is when somebody answers to a
`Poll`.  A Response contains a set of :class:`AnswerChoices
<AnswerChoice>`, each of which represents a given Choice selected by
the questioned person for a given `Question` of the `Poll`.  If the
Question is *multiple choice*, then there may be more than one
`AnswerChoice` per `Question`.  A `Response` also contains a set of
`AnswerRemarks`, each of with represents a remark written by the
responding person for a given Question of the Poll.

See also :doc:`/tested/polly`.

"""

import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import pgettext_lazy as pgettext

# om atelier import rstgen
from lino.api import dd, rt
from lino import mixins
from lino.utils import join_elems

from lino.utils.xmlgen import html as xghtml
from lino.utils.xmlgen.html import E

from lino.mixins import Referrable

from lino.modlib.users.mixins import ByUser, UserAuthored

from .utils import ResponseStates, PollStates

config = dd.plugins.polls

NullBooleanField = models.NullBooleanField

NUMBERED_TITLE_FORMAT = "%s) %s"


class ChoiceSet(mixins.BabelNamed):

    class Meta:
        verbose_name = _("Choice Set")
        verbose_name_plural = _("Choice Sets")


class ChoiceSets(dd.Table):
    model = ChoiceSet
    detail_layout = """
    name
    ChoicesBySet
    """


class Choice(mixins.BabelNamed, mixins.Sequenced):

    class Meta:
        verbose_name = _("Choice")
        verbose_name_plural = _("Choices")

    choiceset = models.ForeignKey('polls.ChoiceSet', related_name='choices')

    def get_siblings(self):
        return self.choiceset.choices.order_by('seqno')

    @dd.action()
    def select_by_response(self, ar):
        mi = ar.master_instance
        dd.logger.info("20140929 %s", mi)
        if isinstance(mi, Response):
            AnswerChoice(response=mi, choice=self).save()


class Choices(dd.Table):
    model = 'polls.Choice'


class ChoicesBySet(Choices):
    master_key = 'choiceset'


class Poll(UserAuthored, mixins.CreatedModified, Referrable):
    """A series of questions."""
    class Meta:
        abstract = dd.is_abstract_model(__name__, 'Poll')
        verbose_name = _("Poll")
        verbose_name_plural = _("Polls")
        ordering = ['ref']

    title = models.CharField(_("Heading"), max_length=200)

    details = models.TextField(_("Details"), blank=True)

    default_choiceset = models.ForeignKey(
        'polls.ChoiceSet',
        null=True, blank=True,
        related_name='polls',
        verbose_name=_("Default Choiceset"))

    default_multiple_choices = models.BooleanField(
        _("Allow multiple choices"), default=False)

    questions_to_add = models.TextField(
        _("Questions to add"),
        help_text=_("Paste text for questions to add. "
                    "Every non-empty line will create one question."),
        blank=True)

    state = PollStates.field(default=PollStates.draft)

    workflow_state_field = 'state'

    def __unicode__(self):
        return self.ref or self.title

    def after_ui_save(self, ar):
        if self.questions_to_add:
            # print "20150203 self.questions_to_add", self,
            # self.questions_to_add
            q = None
            qkw = dict()
            number = 1
            for ln in self.questions_to_add.splitlines():
                ln = ln.strip()
                if ln:
                    if ln.startswith('#'):
                        q.details = ln[1:]
                        q.save()
                        continue
                    elif ln.startswith('='):
                        q = Question(poll=self, title=ln[1:],
                                     is_heading=True, **qkw)
                        number = 1
                    else:
                        q = Question(poll=self, title=ln,
                                     number=str(number), **qkw)
                        number += 1
                    q.full_clean()
                    q.save()
                    qkw.update(seqno=q.seqno + 1)
            self.questions_to_add = ''
            self.save()  # save again because we modified afterwards

        super(Poll, self).after_ui_save(ar)

    @dd.virtualfield(dd.HtmlBox(_("Result")))
    def result(self, ar):
        return E.div(*tuple(get_poll_result(self)))


def get_poll_result(self):
    #~ yield E.h1(self.title)
    for cs in ChoiceSet.objects.all():
        questions = self.questions.filter(choiceset=cs)
        if questions.count() > 0:
            yield E.h2(unicode(cs))
            for question in questions:
                yield E.p(question.text)


class PollDetail(dd.DetailLayout):
    main = "general results"

    general = dd.Panel("""
    ref title workflow_buttons
    details
    default_choiceset default_multiple_choices
    polls.QuestionsByPoll
    """, label=_("General"))

    results = dd.Panel("""
    id user created modified state
    polls.ResponsesByPoll
    # result
    PollResult
    """, label=_("Results"))


class Polls(dd.Table):
    model = 'polls.Poll'
    column_names = 'ref title user state *'
    detail_layout = PollDetail()
    insert_layout = dd.InsertLayout("""
    ref title
    default_choiceset default_multiple_choices
    questions_to_add
    """, window_size=(60, 15))


class MyPolls(ByUser, Polls):
    column_names = 'ref title state *'


class Question(mixins.Sequenced):
    """A question of a poll."""
    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['seqno']

    allow_cascaded_delete = ['poll']

    poll = models.ForeignKey('polls.Poll', related_name='questions')
    number = models.CharField(_("No."), max_length=20, blank=True)
    title = models.CharField(pgettext("polls", "Title"), max_length=200)
    details = models.TextField(_("Details"), blank=True)

    # text = models.TextField(verbose_name=_("Text"))
    choiceset = models.ForeignKey('polls.ChoiceSet', blank=True, null=True)
    multiple_choices = models.BooleanField(
        _("Allow multiple choices"), blank=True)
    is_heading = models.BooleanField(_("Heading"), default=False)

    def __unicode__(self):
        #~ return self.text[:40].strip() + ' ...'
        if self.number:
            return NUMBERED_TITLE_FORMAT % (self.number, self.title)
        return self.title

    def get_siblings(self):
        #~ return self.choiceset.choices.order_by('seqno')
        return self.poll.questions.order_by('seqno')

    def get_choiceset(self):
        if self.is_heading:
            return None
        if self.choiceset is None:
            return self.poll.default_choiceset
        return self.choiceset

    def full_clean(self, *args, **kw):
        if self.multiple_choices is None:
            self.multiple_choices = self.poll.default_multiple_choices
        #~ if self.choiceset_id is None:
            #~ self.choiceset = self.poll.default_choiceset
        super(Question, self).full_clean()


class Questions(dd.Table):
    model = 'polls.Question'
    column_names = "seqno poll number title choiceset is_heading *"
    detail_layout = """
    poll number is_heading choiceset multiple_choices
    title
    details
    """
    order_by = ['poll', 'seqno']


class QuestionsByPoll(Questions):
    master_key = 'poll'
    column_names = 'seqno number title is_heading *'
    auto_fit_column_widths = True


class ToggleChoice(dd.Action):
    """Toggle the given choice for the given question in this response.
    """
    readonly = False
    show_in_bbar = False
    parameters = dict(
        question=dd.ForeignKey("polls.Question"),
        choice=dd.ForeignKey("polls.Choice"),
    )
    no_params_window = True

    def run_from_ui(self, ar, **kw):
        response = ar.selected_rows[0]
        if response is None:
            return
        pv = ar.action_param_values
        qs = AnswerChoice.objects.filter(response=response, **pv)
        if qs.count() == 1:
            qs[0].delete()
        elif qs.count() == 0:
            if not pv.question.multiple_choices:
                # delete any other choice which might exist
                qs = AnswerChoice.objects.filter(
                    response=response, question=pv.question)
                qs.delete()
            obj = AnswerChoice(response=response, **pv)
            obj.full_clean()
            obj.save()
        else:
            raise Exception(
                "Oops: %s returned %d rows." % (qs.query, qs.count()))
        ar.success(refresh=True)
        # dd.logger.info("20140930 %s", obj)
            

class Response(UserAuthored, mixins.Registrable):

    class Meta:
        verbose_name = _("Response")
        verbose_name_plural = _("Responses")
        ordering = ['date']

    poll = dd.ForeignKey('polls.Poll', related_name='responses')
    date = models.DateField(_("Date"), default=dd.today)
    state = ResponseStates.field(default=ResponseStates.draft)
    remark = models.TextField(verbose_name=_("My general remark"), blank=True)
    partner = dd.ForeignKey('contacts.Partner', blank=True, null=True)

    toggle_choice = ToggleChoice()

    @dd.chooser()
    def poll_choices(cls):
        return Poll.objects.filter(state=PollStates.published)

    def __unicode__(self):
        if self.partner is None:
            return _("%(user)s's response to %(poll)s") % dict(
                user=self.user, poll=self.poll)
        return _("{poll} {partner} {date}").format(
            user=self.user.initials,
            date=dd.fds(self.date),
            partner=self.partner.get_full_name(salutation=False),
            poll=self.poll)

    @classmethod
    def get_registrable_fields(model, site):
        for f in super(Response, model).get_registrable_fields(site):
            yield f
        yield 'user'
        yield 'poll'
        yield 'date'
        yield 'partner'


class ResponseDetail(dd.DetailLayout):
    main = "answers more"
    answers = dd.Panel("""
    poll partner date workflow_buttons
    polls.AnswersByResponse
    """, label=_("General"))
    more = dd.Panel("""
    user state
    remark
    """, label=_("More"))


class Responses(dd.Table):
    model = 'polls.Response'
    detail_layout = ResponseDetail()
    insert_layout = """
    user date
    poll
    """

    # workflow_state_field = 'state'

    @classmethod
    def unused_get_detail_title(self, ar, obj):
        txt = _("response to %(poll)s") % dict(poll=obj.poll)
        if obj.user == ar.get_user():
            return _("My %s") % txt
        return _("%(user)s's %(what)s") % dict(user=obj.user, what=txt)


class MyResponses(ByUser, Responses):
    column_names = 'date poll state remark *'


class ResponsesByPoll(Responses):
    master_key = 'poll'
    column_names = 'date user state partner remark *'


class ResponsesByPartner(Responses):
    """Show all responses for a given partner.  Default view is
    :meth:`get_slave_summary`.

    """
    master_key = 'partner'
    column_names = 'date user state remark *'
    slave_grid_format = 'summary'

    @classmethod
    def get_slave_summary(self, obj, ar):
        """Displays a summary of all responses for this partner. This is a
        bullet list grouped by poll.

        """
        if obj is None:
            return

        visible_polls = Poll.objects.filter(state__in=(
            PollStates.published, PollStates.closed)).order_by('ref')

        qs = Response.objects.filter(partner=obj).order_by('date')
        polls_responses = {}
        for resp in qs:
            polls_responses.setdefault(resp.poll.pk, []).append(resp)
            
        sar = self.request_from(ar, obj)
        items = []
        for poll in visible_polls:
            elems = [unicode(poll), ' : ']
            responses = polls_responses.get(poll.pk, [])
            elems += join_elems(
                [ar.obj2html(r, dd.fds(r.date))
                 for r in responses], sep=', ')
            if poll.state == PollStates.published:
                elems += [' ', sar.insert_button(known_values=dict(
                    poll=poll))]
            items.append(E.li(*elems))
        return E.div(E.ul(*items))


class AnswerChoice(dd.Model):

    class Meta:
        verbose_name = _("Answer Choice")
        verbose_name_plural = _("Answer Choices")
        ordering = ['question__seqno']

    response = models.ForeignKey('polls.Response')
    question = models.ForeignKey('polls.Question')
    choice = models.ForeignKey(
        'polls.Choice',
        related_name='answers', verbose_name=_("My answer"),
        blank=True, null=True)

    @dd.chooser()
    def choice_choices(cls, question):
        return question.get_choiceset().choices.all()


class AnswerChoices(dd.Table):
    model = 'polls.AnswerChoice'


class AnswerRemark(dd.Model):

    class Meta:
        verbose_name = _("Answer Remark")
        verbose_name_plural = _("Answer Remarks")
        ordering = ['question__seqno']

    response = models.ForeignKey('polls.Response')
    question = models.ForeignKey('polls.Question')
    remark = models.TextField(_("My remark"), blank=True)


class AnswerRemarks(dd.Table):
    model = 'polls.AnswerRemarks'

FORWARD_TO_QUESTION = tuple("full_clean after_ui_save disable_delete".split())


class Answer(object):
    """Volatile object to represent the one and only answer to a given
    question in a given response.

    """

    def __init__(self, response, question):
        self.response = response
        self.question = question
        self.pk = self.id = question.pk
        try:
            self.remark = AnswerRemark.objects.get(
                question=question, response=response)
        except AnswerRemark.DoesNotExist:
            self.remark = AnswerRemark(question=question, response=response)

        self.choices = AnswerChoice.objects.filter(
            question=question, response=response)
        for k in FORWARD_TO_QUESTION:
            setattr(self, k, getattr(question, k))

    def __unicode__(self):
        if self.choices.count() == 0:
            return unicode(_("N/A"))
        return ', '.join([unicode(ac.choice) for ac in self.choices])


class AnswerRemarkField(dd.VirtualField):

    """
    An editable virtual field.
    """
    editable = True

    def __init__(self):
        t = models.TextField(_("My remark"), blank=True)
        dd.VirtualField.__init__(self, t, None)

    def set_value_in_object(self, ar, obj, value):
        #~ e = self.get_entry_from_answer(obj)
        obj.remark.remark = value
        obj.remark.save()

    def value_from_object(self, obj, ar):
        #~ logger.info("20120118 value_from_object() %s",dd.obj2str(obj))
        #~ e = self.get_entry_from_answer(obj)
        return obj.remark.remark


class AnswersByResponse(dd.VirtualTable):
    """The table used for answering to a poll.

.. attribute:: answer_buttons

    A virtual field that displays the currently selected answer(s) for
    this question, eventually (if editing is permitted) together with
    buttons to modify the selection.

    """
    label = _("Answers")
    editable = True
    master = 'polls.Response'
    column_names = 'question:40 answer_buttons:30 remark:20 *'
    variable_row_height = True
    auto_fit_column_widths = True
    slave_grid_format = 'summary'
    # workflow_state_field = 'state'

    remark = AnswerRemarkField()

    @classmethod
    def get_data_rows(self, ar):
        response = ar.master_instance
        if response is None:
            return
        for q in Question.objects.filter(poll=response.poll):
            yield Answer(response, q)

    @classmethod
    def get_slave_summary(self, response, ar):
        """Presents this response as a table with one row per question and one
        column for each response of the same poll.  The answers for
        this response are editable if this response is not registered.
        The answers of other responses are never editable.

        """
        if response is None:
            return
        if response.poll_id is None:
            return
        all_responses = rt.modules.polls.Response.objects.filter(
            poll=response.poll, partner=response.partner).order_by('date')
        ht = xghtml.Table()
        ht.attrib.update(cellspacing="3px", bgcolor="#ffffff", width="100%")
        cellattrs = dict(align="left", valign="top", bgcolor="#eeeeee")
        headers = [_("Question")]
        for r in all_responses:
            if r == response:
                headers.append(dd.fds(r.date))
            else:
                headers.append(ar.obj2html(r, dd.fds(r.date)))
        ht.add_header_row(*headers, **cellattrs)
        ar.master_instance = response  # must set it because
                                       # get_data_rows() needs it.
        for answer in self.get_data_rows(ar):
            cells = [self.question.value_from_object(answer, ar)]
            for r in all_responses:
                if r == response:
                    btn = self.answer_buttons.value_from_object(answer, ar)
                else:
                    other_answer = Answer(r, answer.question)
                    btn = unicode(other_answer)
                cells.append(btn)
            ht.add_body_row(*cells, **cellattrs)
        
        return ht.as_element()  # rstgen.table(headers, rows)

    @dd.displayfield(_("My answer"))
    def answer_buttons(self, obj, ar):
        # assert isinstance(obj, Answer)
        cs = obj.question.get_choiceset()
        if cs is None:
            return ''

        elems = []
        pv = dict(question=obj.question)
        # ia = obj.response.toggle_choice

        # ba = Responses.get_action_by_name('toggle_choice')
        ba = Responses.actions.toggle_choice
        if ba is None:
            raise Exception("No toggle_choice on {0}?".format(ar.actor))
        sar = ba.request_from(ar)

        # print("20150203 answer_buttons({0})".format(sar))

        # if the response is registered, just display the choice, no
        # toggle buttons since answer cannot be toggled:
        if not sar.get_permission(obj.response):
            return unicode(obj)

        for c in cs.choices.all():
            pv.update(choice=c)
            text = unicode(c)
            qs = AnswerChoice.objects.filter(response=obj.response, **pv)
            if qs.count() == 1:
                text = [E.b('[', text, ']')]
            elif qs.count() == 0:
                pass
            else:
                raise Exception(
                    "Oops: %s returned %d rows." % (qs.query, qs.count()))
            sar.set_action_param_values(**pv)
            e = sar.ar2button(obj.response, text, style="text-decoration:none")
            elems.append(e)
        return E.span(*join_elems(elems))

    # @classmethod
    # def get_row_state(self, obj):
    #     return obj.response.state

    @classmethod
    def get_pk_field(self):
        return Question._meta.pk
        #~ return AnswerPKField()

    @classmethod
    def get_row_by_pk(self, ar, pk):
        response = ar.master_instance
        #~ if response is None: return
        q = Question.objects.get(pk=pk)
        return Answer(response, q)

    # @classmethod
    # def get_row_permission(cls, obj, ar, state, ba):
    #     return obj.response.get_row_permission(ar, state, ba)

    @classmethod
    def disable_delete(self, obj, ar):
        return "Not deletable"

    @dd.displayfield(_("Question"))
    def question(self, obj, ar):
        if obj.question.number:
            txt = NUMBERED_TITLE_FORMAT % (
                obj.question.number, obj.question.title)
        else:
            txt = obj.question.title
        if obj.question.details:
            attrs = dict(title=obj.question.details)
        else:
            attrs = dict()
        if obj.question.is_heading:
            txt = E.b(txt, **attrs)
        return E.span(txt, **attrs)


class PollResult(Questions):
    "Shows a summay of responses to this poll."
    master_key = 'poll'
    column_names = "question choiceset answers a1"

    @classmethod
    def get_data_rows(self, ar):
        poll = ar.master_instance
        if poll is None:
            return
        for obj in super(PollResult, self).get_request_queryset(ar):
            yield obj

    @dd.virtualfield(dd.ForeignKey('polls.Question'))
    def question(self, obj, ar):
        return obj

    @dd.requestfield(_("#Answers"))
    def answers(self, obj, ar):
        #~ return ar.spawn(Answer.objects.filter(question=obj))
        return AnswerChoices.request(known_values=dict(question=obj))

    @dd.requestfield(_("A1"))
    def a1(self, obj, ar):
        cs = obj.get_choiceset()
        if cs is not None:
            c = iter(cs.choices.all()).next()
            #~ return Answer.objects.filter(question=obj,choice=c)
            return AnswerChoices.request(
                known_values=dict(question=obj, choice=c))


dd.add_user_group(config.app_label, config.verbose_name)
