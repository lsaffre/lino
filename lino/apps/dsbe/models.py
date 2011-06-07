# -*- coding: UTF-8 -*-
## Copyright 2008-2011 Luc Saffre
## This file is part of the Lino project.
## Lino is free software; you can redistribute it and/or modify 
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
## Lino is distributed in the hope that it will be useful, 
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
## GNU General Public License for more details.
## You should have received a copy of the GNU General Public License
## along with Lino; if not, see <http://www.gnu.org/licenses/>.

"""
See also :doc:`/dsbe/models`.

"""

import os
import cgi
import datetime

from django.db import models
#~ from django.db.models import Q
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode 

#~ import lino
#~ logger.debug(__file__+' : started')

from lino import reports
#~ from lino import layouts
from lino.utils import perms
#~ from lino.utils import printable
from lino import mixins
from lino import actions
from lino import fields
from lino.modlib.contacts import models as contacts
from lino.modlib.notes import models as notes
from lino.modlib.links import models as links
from lino.modlib.uploads import models as uploads
from lino.utils.choicelists import HowWell
#~ from lino.modlib.properties.utils import KnowledgeField #, StrengthField
#~ from lino.modlib.uploads.models import UploadsByPerson
from lino.models import get_site_config
from lino.tools import get_field
from lino.tools import resolve_field
from lino.utils.babel import DEFAULT_LANGUAGE, babelattr, babeldict_getitem
#~ from lino.utils.babel import add_babel_field, DEFAULT_LANGUAGE, babelattr, babeldict_getitem
from lino.utils import babel 
from lino.utils.choosers import chooser
from lino.utils import mti
from lino.mixins.printable import DirectPrintAction
from lino.mixins.reminder import ReminderEntry

from lino.modlib.countries.models import CountryCity


SCHEDULE_CHOICES = {
    'de':[ 
        u"5-Tage-Woche",
        u"Montag, Mittwoch, Freitag",
        u"Individuell",
        ],
    'fr':[ 
        u"5 jours/semaine",
        u"lundi,mercredi,vendredi",
        u"individuel",
        ],
    'en':[
        u"5 days/week",
        u"Monday, Wednesday, Friday",
        u"Individual",
        ]
}

REGIME_CHOICES = {
    'de':[ 
        u"20 Stunden/Woche",
        u"35 Stunden/Woche",
        u"38 Stunden/Woche",
        ],
    'fr':[ 
        u"20 heures/semaine",
        u"35 heures/semaine",
        u"38 heures/semaine",
        ],
    'en':[
        u"20 hours/week",
        u"35 hours/week",
        u"38 hours/week",
        u"38 hours/week",
        ]
}

#~ AID_RATE_CHOICES = {
    #~ 'de':[ 
        #~ u'Alleinlebende Person',
        #~ u'Zusammenlebende Person',
        #~ u'Person mit Familie zu Lasten',
        #~ ],
    #~ 'fr':[ 
        #~ u'Personne isolée',
        #~ u'Personne cohabitante',
        #~ u'Personne qui cohabite avec une famille à sa charge',
        #~ ],
    #~ 'en':[
        #~ ]
#~ }

#~ AID_NATURE_CHOICES = {
    #~ 'de':[ 
        #~ u'Eingliederungseinkommen',
        #~ u'Sozialhilfe', 
        #~ u'Ausgleich zum Eingliederungseinkommen', 
        #~ u'Ausgleich zur Sozialhilfe' 
        #~ ],
    #~ 'fr':[ 
        #~ u"Revenu d'intégration sociale",
        #~ u"Aide sociale",
        #~ u"Complément au revenu d'intégration sociale",
        #~ u"Complément à l'aide sociale",
        #~ ],
    #~ 'en':[
        #~ ]
#~ }

def language_choices(language,choices):
    l = choices.get(language,None)
    if l is None:
        l = choices.get(DEFAULT_LANGUAGE)
    return l


CIVIL_STATE_CHOICES = [
  ('1', _("single")   ),
  ('2', _("married")  ),
  ('3', _("divorced") ),
  ('4', _("widowed")  ),
  ('5', _("separated")  ), # Getrennt von Tisch und Bett / 
]

SEX_CHOICES = (('M',_('Male')),('F',_('Female')))


# http://en.wikipedia.org/wiki/European_driving_licence

#~ DRIVING_LICENSE_CHOICES = (
  #~ ('A'  , _("Motorcycles") ),
  #~ ('B'  , _("Car") ), # Auto
  #~ ('C'  , _("Lorry") ),
  #~ ('CE' , _("Lorry with trailer") ), 
  #~ ('D'  , _("Bus") ), 
#~ )

RESIDENCE_TYPE_CHOICES = (
  (1  , _("Registry of citizens")   ), # Bevölkerungsregister registre de la population
  (2  , _("Registry of foreigners") ), # Fremdenregister        Registre des étrangers      vreemdelingenregister 
  (3  , _("Waiting for registry")   ), # Warteregister
)

BEID_CARD_TYPES = {
  '1' : dict(en=u"Belgian citizen",de=u"Belgischer Staatsbürger",fr=u"Citoyen belge"),
  '6' : dict(en=u"Kids card (< 12 year)",de=u"Kind unter 12 Jahren"),
  '8' : dict(en=u"Habilitation",fr=u"Habilitation",nl=u"Machtiging"),
  '11' : dict(
        en=u"Foreigner card type A",
        nl=u"Bewijs van inschrijving in het vreemdelingenregister - Tijdelijk verblijf",
        fr=u"Certificat d'inscription au registre des étrangers - Séjour temporaire",
        de=u"Bescheinigung der Eintragung im Ausländerregister - Vorübergehender Aufenthalt",
      ),
  '12' : dict(
        en=u"Foreigner card type B",
        nl=u"Bewijs van inschrijving in het vreemdelingenregister",
        fr=u"Certificat d'inscription au registre des étrangers",
        de=u"Bescheinigung der Eintragung im Ausländerregister",
      ),
  '13' : dict(
        en=u"Foreigner card type C",
        nl=u"Identiteitskaart voor vreemdeling",
        fr=u"Carte d'identité d'étranger",
        de=u"Personalausweis für Ausländer",
      ),
  '14' : dict(
        en=u"Foreigner card type D",
        nl=u"EG - langdurig ingezetene",
        fr=u"Résident de longue durée - CE",
        de=u"Daueraufenthalt - EG",
      ),
  '15' : dict(
        en=u"Foreigner card type E",
        nl=u"Verklaring van inschrijving",
        fr=u"Attestation d’enregistrement",
        de=u"Anmeldebescheinigung",
      ),
  '16' : dict(
        en=u"Foreigner card type E+",
      ),
  '17' : dict(
        en=u"Foreigner card type F",
        nl=u"Verblijfskaart van een familielid van een burger van de Unie",
        fr=u"Carte de séjour de membre de la famille d’un citoyen de l’Union",
        de=u"Aufenthaltskarte für Familienangehörige eines Unionsbürgers",
      ),
  '18' : dict(
        en=u"Foreigner card type F+",
      ),
}



class Partner(mixins.DiffingMixin,models.Model):
    """
    """
    class Meta:
        app_label = 'contacts'
        abstract = True
  
    id = models.AutoField(primary_key=True,verbose_name=_("Partner #"))
    #~ id = models.CharField(max_length=10,primary_key=True,verbose_name=_("ID"))
    
    is_active = models.BooleanField(verbose_name=_("is active"),default=True)
    "Indicates whether this Contact may be used when creating new operations."
    
    activity = models.ForeignKey("dsbe.Activity",blank=True,null=True,
        verbose_name=_("Activity"))
    "Pointer to :class:`dsbe.Activity`. May be empty."
    
    bank_account1 = models.CharField(max_length=40,blank=True,null=True,
        verbose_name=_("Bank account 1"))
        
    bank_account2 = models.CharField(max_length=40,blank=True,null=True,
        verbose_name=_("Bank account 2"))
        
    #~ def save(self,*args,**kw):
        #~ self.before_save()
        #~ r = super(Partner,self).save(*args,**kw)
        #~ return r
        
    #~ def before_save(self):
    def full_clean(self,*args,**kw):
        if self.id is None:
            sc = get_site_config()
            if sc.next_partner_id is not None:
                self.id = sc.next_partner_id
                sc.next_partner_id += 1
                sc.save()
        super(Partner,self).full_clean(*args,**kw)
        
    def disable_delete(self,request):
        if settings.TIM2LINO_IS_IMPORTED_PARTNER(self):
            return _("Cannot delete companies and persons imported from TIM")
          



class Person(Partner,contacts.Person):
    """
    Represents a physical person.
    
    """
    
    class Meta(contacts.Person.Meta):
        app_label = 'contacts'
        verbose_name = _("person") # :doc:`/tickets/14`
        verbose_name_plural = _("persons") # :doc:`/tickets/14`
        
    #~ first_name = models.CharField(max_length=200,blank=True,verbose_name=_('First name'))
    #~ last_name = models.CharField(max_length=200,blank=True,verbose_name=_('Last name'))
    #~ title = models.CharField(max_length=200,blank=True,verbose_name=_('Title'))
        
    def disabled_fields(self,request):
        if settings.TIM2LINO_IS_IMPORTED_PARTNER(self):
            return settings.LINO.PERSON_TIM_FIELDS
        return []
        
    def get_queryset(self):
        return self.model.objects.select_related('country','city','coach1','coach2','nationality')
        
    #~ def full_clean(self,*args,**kw):
        #~ l = filter(lambda x:x,[self.last_name,self.first_name,self.title])
        #~ self.name = " ".join(l)
        #~ super(Person,self).full_clean(*args,**kw)
        
    #~ def clean(self):
        #~ l = filter(lambda x:x,[self.last_name,self.first_name,self.title])
        #~ self.name = " ".join(l)
        #~ super(Person,self).clean()
        
    remarks2 = models.TextField(_("Remarks (Social Office)"),blank=True,null=True)
    gesdos_id = models.CharField(max_length=40,blank=True,null=True,
        verbose_name=_("Gesdos ID"))
        
    is_cpas = models.BooleanField(verbose_name=_("receives social help"))
    is_senior = models.BooleanField(verbose_name=_("is senior"))
    #~ is_minor = models.BooleanField(verbose_name=_("is minor"))
    group = models.ForeignKey("dsbe.PersonGroup",blank=True,null=True,
        verbose_name=_("Integration phase"))
    #~ is_dsbe = models.BooleanField(verbose_name=_("is coached"),default=False)
    "Indicates whether this Person is coached."
    
    coached_from = models.DateField(
        blank=True,null=True,
        verbose_name=_("Coached from"))
    coached_until = models.DateField(
        blank=True,null=True,
        verbose_name=_("until"))
    
    coach1 = models.ForeignKey("users.User",blank=True,null=True,
        verbose_name=_("Coach 1"),related_name='coached1')
    coach2 = models.ForeignKey("users.User",blank=True,null=True,
        verbose_name=_("Coach 2"),related_name='coached2')
        
    sex = models.CharField(max_length=1,blank=True,null=True,
        verbose_name=_("Sex"),
        choices=SEX_CHOICES) 
    birth_date = models.DateField(
        blank=True,null=True,
        verbose_name=_("Birth date"))
    birth_date_circa = models.BooleanField(
        default=False,
        verbose_name=_("not exact"))
    birth_place = models.CharField(_("Birth place"),
        max_length=200,
        blank=True,null=True)
    birth_country = models.ForeignKey("countries.Country",
        blank=True,null=True,
        verbose_name=_("Birth country"),related_name='by_birth_place')
    civil_state = models.CharField(max_length=1,
        blank=True,null=True,
        verbose_name=_("Civil state"),
        choices=CIVIL_STATE_CHOICES) 
    national_id = models.CharField(max_length=200,blank=True,verbose_name=_("National ID"))
    
    health_insurance = models.ForeignKey("contacts.Company",blank=True,null=True,
        verbose_name=_("Health insurance"),related_name='health_insurance_for')
    pharmacy = models.ForeignKey("contacts.Company",blank=True,null=True,
        verbose_name=_("Pharmacy"),related_name='pharmacy_for')
    
    nationality = models.ForeignKey('countries.Country',
        blank=True,null=True,
        related_name='by_nationality',
        verbose_name=_("Nationality"))
    #~ tim_nr = models.CharField(max_length=10,blank=True,null=True,unique=True,
        #~ verbose_name=_("TIM ID"))
    card_number = models.CharField(max_length=20,blank=True,null=True,
        verbose_name=_("eID card number"))
    card_valid_from = models.DateField(
        blank=True,null=True,
        verbose_name=_("ID card valid from"))
    card_valid_until = models.DateField(
        blank=True,null=True,
        verbose_name=_("until"))
        
    card_type = models.CharField(max_length=20,blank=True,null=True,
        verbose_name=_("eID card type"))
    "The type of the electronic ID card. Imported from TIM."
    
    card_issuer = models.CharField(max_length=50,
        blank=True,null=True,
        verbose_name=_("eID card issuer"))
    "The administration who issued this ID card. Imported from TIM."
    
    noble_condition = models.CharField(max_length=50,blank=True,null=True,
        verbose_name=_("noble condition"))
    "The eventual noble condition of this person. Imported from TIM."
        
        
    #~ driving_license = models.ForeignKey("dsbe.DrivingLicense",blank=True,null=True,
        #~ verbose_name=_("Driving license"))
    #~ driving_license = models.CharField(max_length=4,blank=True,null=True,
        #~ verbose_name=_("Driving license"),choices=DRIVING_LICENSE_CHOICES)
    
    #~ no_shift            = models.BooleanField(verbose_name=_("no shift work"))
    #~ no_weekend          = models.BooleanField(verbose_name=_("no work on week-end"))
    #~ has_family          = models.BooleanField(verbose_name=_("Head of a family"))
    #~ has_own_car         = models.BooleanField(verbose_name=_("has own car"))
    #~ can_car             = models.BooleanField(verbose_name=_("Car driving licence"))
    #~ can_truck           = models.BooleanField(verbose_name=_("Truck driving licence"))
    #~ can_clark           = models.BooleanField(verbose_name=_("Clark driving licence"))
    #~ can_bus             = models.BooleanField(verbose_name=_("Bus driving licence"))
    #~ it_knowledge        = fields.KnowledgeField(blank=True,null=True,verbose_name=_("IT knowledge"))
    #~ physical_handicap   = models.BooleanField(_("Physical handicap"))
    #~ mental_handicap     = models.BooleanField(_("Mental handicap"))
    #~ psycho_handicap     = models.BooleanField(_("Psychological handicap"))
    #~ health_problems     = models.BooleanField(_("Health problems"))
    #~ juristic_problems   = models.BooleanField(_("Juristic problems"))
    #~ dependency_problems = models.BooleanField(_("Dependency problems"))
    #~ social_competence   = models.BooleanField(_("Lack of social competence"))
    #~ motivation_lack     = models.BooleanField(_("Lack of motivation"))
    #~ fulltime_only       = models.BooleanField(_("Fulltime only"))
    #~ parttime_only       = models.BooleanField(_("Part-time only"))
    #~ young_children      = models.BooleanField(_("Young children"))
    #~ is_illiterate       = models.BooleanField(_("Illiterate"))
        
    residence_type = models.SmallIntegerField(blank=True,null=True,
        verbose_name=_("Residence type"),
        choices=RESIDENCE_TYPE_CHOICES,
        max_length=1,
        #~ limit_to_choices=True,
        )
    in_belgium_since = models.DateField(_("Lives in Belgium since"),blank=True,null=True)
    unemployed_since = models.DateField(_("Seeking work since"),blank=True,null=True)
    #~ work_permit_exempt = models.BooleanField(verbose_name=_("Work permit exemption"))
    needs_residence_permit = models.BooleanField(verbose_name=_("Needs residence permit"))
    needs_work_permit = models.BooleanField(verbose_name=_("Needs work permit"))
    #~ work_permit_valid_until = models.DateField(blank=True,null=True,verbose_name=_("Work permit valid until"))
    work_permit_suspended_until = models.DateField(blank=True,null=True,verbose_name=_("suspended until"))
    aid_type = models.ForeignKey("dsbe.AidType",blank=True,null=True,
        verbose_name=_("aid type"))
        
    income_ag    = models.BooleanField(verbose_name=_("Arbeitslosengeld"))
    income_wg    = models.BooleanField(verbose_name=_("Wartegeld"))
    income_kg    = models.BooleanField(verbose_name=_("Krankengeld"))
    income_rente = models.BooleanField(verbose_name=_("Rente"))
    income_misc  = models.BooleanField(verbose_name=_("Andere"))
    
    is_seeking = models.BooleanField(_("is seeking work"))
    unavailable_until = models.DateField(blank=True,null=True,verbose_name=_("Unavailable until"))
    unavailable_why = models.CharField(max_length=100,blank=True,null=True,
        verbose_name=_("reason"))
    
    native_language = models.ForeignKey('countries.Language',
      verbose_name=_("Native language"),
      blank=True,null=True)
      
    obstacles = models.TextField(_("Obstacles"),blank=True,null=True)
    skills = models.TextField(_("Other skills"),blank=True,null=True)
    job_agents = models.CharField(max_length=100,
        blank=True,null=True,
        verbose_name=_("Job agents"))
    
    job_office_contact = models.ForeignKey("contacts.Contact",
      blank=True,null=True,
      verbose_name=_("Contact person at local job office"),
      related_name='persons_job_office')
      
    @chooser()
    def job_office_contact_choices(cls):
        sc = get_site_config()
        if sc.job_office is not None:
        #~ pk = settings.LINO_SITE.job_office_id
        #~ if pk is not None:
            #~ jo = Company.objects.get(pk=pk)
            #~ return jo.contact_set.all()
            return sc.job_office.contact_set.all()
        return []


    @classmethod
    def setup_report(model,rpt):
        u"""
        rpt.add_action(DirectPrintAction('auskblatt',_("Auskunftsblatt"),'persons/auskunftsblatt.odt'))
        Zur Zeit scheint es so, dass das Auskunftsblatt eher überflüssig wird.
        """
        rpt.add_action(DirectPrintAction('eid',_("eID-Inhalt"),'persons/eid-content.odt'))
        rpt.add_action(DirectPrintAction('cv',_("Curiculum vitae"),'persons/cv.odt'))
        
    def __unicode__(self):
        return u"%s (%s)" % (self.name,self.pk)
        
    def clean(self):
        if self.job_office_contact:
            #~ print "Person.clean()", self
            if self.job_office_contact.person == self:
                raise ValidationError(_("Circular reference"))
        super(Person,self).clean()
        
    full_name = property(contacts.Person.get_full_name)
    
    def card_type_text(self,request):
        if self.card_type:
            s = babeldict_getitem(BEID_CARD_TYPES,self.card_type)
            if s:
                return s
            return _("Unknown card type %r") % self.card_type
        return _("Not specified") # self.card_type
    card_type_text.return_type = fields.DisplayField(_("eID card type"))
        
    def get_print_language(self,pm):
        "Used by DirectPrintAction"
        return self.language
        
    @classmethod
    def get_reminders(model,ui,user,today,back_until):
        q = models.Q(coach1__exact=user) | models.Q(coach2__exact=user)
        
        def find_them(fieldname,today,delta,msg,**linkkw):
            filterkw = { fieldname+'__lte' : today + delta }
            if back_until is not None:
                filterkw.update({ 
                    fieldname+'__gte' : back_until
                })
            for obj in model.objects.filter(q,**filterkw).order_by(fieldname):
                linkkw.update(fmt='detail')
                url = ui.get_detail_url(obj,**linkkw)
                html = '<a href="%s">%s</a>&nbsp;: %s' % (url,unicode(obj),cgi.escape(msg))
                yield ReminderEntry(getattr(obj,fieldname),html)
            
        #~ delay = 30
        #~ for obj in model.objects.filter(q,
              #~ card_valid_until__lte=date+datetime.timedelta(days=delay)).order_by('card_valid_until'):
            #~ yield ReminderEntry(obj,obj.card_valid_until,_("eID card expires in %d days") % delay,fmt='detail',tab=3)
        for o in find_them('card_valid_until', today, datetime.timedelta(days=30),
            _("eID card expires"),tab=0):
            yield o
        for o in find_them('unavailable_until', today, datetime.timedelta(days=30),
            _("becomes available again"),tab=1):
            yield o
        for o in find_them('work_permit_suspended_until', today, datetime.timedelta(days=30),
              _("work permit suspension ends"),tab=1):
            yield o
        for o in find_them('coached_until', today, datetime.timedelta(days=30),
            _("coaching ends"),tab=1):
            yield o
            
        
    def get_image_parts(self):
        if self.card_number:
            return ("beid",self.card_number+".jpg")
        return ("pictures","contacts.Person.jpg")
    def get_image_url(self):
        return settings.MEDIA_URL + "/".join(self.get_image_parts())
    def get_image_path(self):
        return os.path.join(settings.MEDIA_ROOT,*self.get_image_parts())
        
            
    def age(self,request):
        if self.birth_date:
            dd = datetime.date.today()-self.birth_date
            return _("%d years") % (dd.days / 365)
        return _('unknown')
    age.return_type = fields.DisplayField(_("Age"))
    #~ age.return_type = models.CharField(_("Age"),max_length=10,editable=False,blank=True)
    
    def overview(self,request):
        def qsfmt(qs):
            s = qs.model._meta.verbose_name_plural + ': '
            if qs.count():
                s += ', '.join([unicode(lk) for lk in qs])
            else:
                s += '<b>%s</b>' % force_unicode(_("not filled in"))
            return force_unicode(s)
        
        lines = []
        #~ lines.append('<div>')
        lines.append(qsfmt(self.languageknowledge_set.all()))
        lines.append(qsfmt(self.study_set.all()))
        lines.append(qsfmt(self.contract_set.all()))
        #~ from django.utils.translation import string_concat
        #~ lines.append('</div>')
        return '<br/>'.join(lines)
    overview.return_type = fields.HtmlBox(_("Overview"))
    
    def residence_permit(self,rr):
        kv = dict(type=settings.LINO.config.residence_permit_upload_type)
        r = rr.spawn_request(uploads.UploadsByOwner(),
              master_instance=self,
              known_values=kv)
        return rr.ui.quick_upload_buttons(r)
        #~ rrr = uploads.UploadsByPerson().request(rr.ui,master_instance=self,known_values=kv)
        #~ return rr.ui.quick_upload_buttons(rrr)
    residence_permit.return_type = fields.DisplayField(_("Residence permit"))
    
    def work_permit(self,rr):
        kv = dict(type=settings.LINO.config.work_permit_upload_type)
        r = rr.spawn_request(uploads.UploadsByOwner(),
              master_instance=self,
              known_values=kv)
        return rr.ui.quick_upload_buttons(r)
    work_permit.return_type = fields.DisplayField(_("Work permit"))
    
    def driving_licence(self,rr):
        kv = dict(type=settings.LINO.config.driving_licence_upload_type)
        r = rr.spawn_request(uploads.UploadsByOwner(),
              master_instance=self,known_values=kv)
        return rr.ui.quick_upload_buttons(r)
    driving_licence.return_type = fields.DisplayField(_("driving licence"))
    
    @classmethod
    def site_setup(cls,lino):
        lino.PERSON_TIM_FIELDS = reports.fields_list(cls,
          '''name first_name last_name title remarks remarks2
          zip_code city country street street_no street_box 
          birth_date sex birth_place coach1 language 
          phone fax email 
          card_number card_valid_from card_valid_until
          noble_condition card_issuer
          national_id health_insurance pharmacy 
          bank_account1 bank_account2 
          gesdos_id activity 
          is_cpas is_senior is_active nationality''')



class Persons(contacts.Persons):
    can_view = perms.is_authenticated
    app_label = 'contacts'
    #~ extra = dict(
      #~ select=dict(sort_name='lower(last_name||first_name)'),
      #~ order_by=['sort_name'])
    #~ order_by = None # clear the default value from contacts.Persons.order_by since we use extra order_by

    
class PersonsByNationality(Persons):
    #~ app_label = 'contacts'
    fk_name = 'nationality'
    order_by = "city name".split()
    column_names = "city street street_no street_box addr2 name country language *"
    
class PersonsByCity(Persons):
    #~ app_label = 'contacts'
    fk_name = 'city'
    order_by = 'street street_no street_box addr2'.split()
    column_names = "street street_no street_box addr2 name language *"
    
def only_coached_persons(qs,period_from,period_until=None):
    """
    coached_from and coached_until
    """
    #~ period_from = period_from or datetime.date.today()
    period_until = period_until or period_from
    #~ today = datetime.date.today()
    Q = models.Q
    qs = qs.filter(Q(coached_until__isnull=False)|Q(coached_from__isnull=False))
    if period_from is not None:
        qs = qs.filter(Q(coached_until__isnull=True)|Q(coached_until__gte=period_from))
    if period_until is not None:
        qs = qs.filter(Q(coached_from__isnull=True)|Q(coached_from__lte=period_until))
    return qs
    #~ return qs.filter(
        #~ models.Q(coached_from__isnull=False,coached_from__lte=period_until) | 
        #~ models.Q(coached_until__isnull=False,coached_until__gte=period_from)
        #~ )
  
def only_my_persons(qs,user):
    return qs.filter(models.Q(coach1__exact=user) | models.Q(coach2__exact=user))

class MyPersons(Persons):
    use_as_default_report = False
    label = _("My coached Persons")
    order_by = ['last_name','first_name']
    #~ def get_queryset(self):
    def get_request_queryset(self,rr):
        qs = super(MyPersons,self).get_request_queryset(rr)
        return only_coached_persons(only_my_persons(qs,rr.user),datetime.date.today())
        #~ today = datetime.date.today()
        #~ Q = models.Q
        #~ q1 = Q(coach1__exact=rr.user) | Q(coach2__exact=rr.user)
        #~ q2 = Q(coached_from__isnull=False) | Q(coached_until__isnull=False,coached_until__gte=today)
        #~ return qs.filter(q1,q2)

class MyPersonsByGroup(MyPersons):
    fk_name = 'group'
    
 

def persons_by_user():
    """Returns a summary table "Number of coached persons by user and integration phase"
    """
    #~ from django.utils.translation import ugettext as _
    #~ from lino.modlib.users.models import User  
    User = resolve_model('users.User')
    #~ from lino.apps.dsbe.models import PersonGroup,Person,only_coached_persons,only_my_persons
    headers = [cgi.escape(_("User")),cgi.escape(_("Total"))]
    sums = []
    pg2col = {}
    for pg in PersonGroup.objects.order_by('name'):
        headers.append('<font size="2">%s</font>' % cgi.escape(pg.name))
        sums.append(0)
        pg2col[pg.pk] = len(headers) - 1
        
    rows = [ headers ]
    for user in User.objects.order_by('username'):
        persons = only_coached_persons(only_my_persons(Person.objects.all(),user),datetime.date.today())
        cells = [cgi.escape(unicode(user)),persons.count()] + sums
        for person in persons:
            if person.group is not None:
                cells[pg2col[person.group.pk]] += 1
        rows.append(cells)
        
    s = ''
    for row in rows:
        s += '<tr>'
        s += ''.join(['<td align="center" valign="middle" bgcolor="#eeeeee" width="30%%">%s</td>' % cell for cell in row])
        s += '</tr>'
    s = '<table cellspacing="3px" bgcolor="#ffffff"><tr>%s</tr></table>' % s
    s = '<div class="htmlText">%s</div>' % s
    return s
    
              
#~ class Company(Contact,contacts.Company):
#~ class Company(Partner,contacts.Addressable,):
class Company(Partner,contacts.Company):
  
    """
    Implements :class:`contacts.Company`.
    
    Inner class Meta is necessary because of :doc:`/tickets/14`.
    """
    
    class Meta(contacts.Company.Meta):
        app_label = 'contacts'
        #~ verbose_name = _("Company")
        #~ verbose_name_plural = _("Companies")
        
    #~ vat_id = models.CharField(max_length=200,blank=True)
    #~ type = models.ForeignKey('contacts.CompanyType',blank=True,null=True,verbose_name=_("Company type"))
    prefix = models.CharField(max_length=200,blank=True) 
    hourly_rate = fields.PriceField(_("hourly rate"),blank=True,null=True)
    #~ is_courseprovider = models.BooleanField(_("Course provider")) 
    is_courseprovider = mti.EnableChild('dsbe.CourseProvider',verbose_name=_("Course provider"))
    
    def disabled_fields(self,request):
        if settings.TIM2LINO_IS_IMPORTED_PARTNER(self):
            return settings.LINO.COMPANY_TIM_FIELDS
        return []
    
    @classmethod
    def site_setup(cls,lino):
        lino.COMPANY_TIM_FIELDS = reports.fields_list(cls,
            '''name remarks
            zip_code city country street street_no street_box 
            language vat_id
            phone fax email 
            bank_account1 bank_account2 activity''')
  
    
class Companies(contacts.Companies):
    app_label = 'contacts'
    #~ pass
    
#~ from lino.modlib.contacts.models import Companies

#
# PERSON GROUP
#
class PersonGroup(models.Model):
    """Integration Phase (previously "Person Group")
    """
    name = models.CharField(_("Designation"),max_length=200)
    #~ text = models.TextField(_("Description"),blank=True,null=True)
    class Meta:
        verbose_name = _("Integration Phase")
        verbose_name_plural = _("Integration Phases")
    def __unicode__(self):
        return self.name

class PersonGroups(reports.Report):
    """List of Integration Phases"""
    model = PersonGroup
    order_by = ["name"]

    
#
# STUDY TYPE
#
class StudyType(models.Model):
    #~ text = models.TextField(_("Description"),blank=True,null=True)
    class Meta:
        verbose_name = _("study type")
        verbose_name_plural = _("study types")
        
    #~ name = models.CharField(_("Designation"),max_length=200)
    name = babel.BabelCharField(_("Designation"),max_length=200)
    
    def __unicode__(self):
        return unicode(babel.babelattr(self,'name'))
    #~ def __unicode__(self):
        #~ return self.name

class StudyTypes(reports.Report):
    #~ label = _('Study types')
    model = StudyType
    order_by = ["name"]

#
# STUDY CONTENT
#
#~ class StudyContent(models.Model):
    #~ type = models.ForeignKey(StudyType)
    #~ name = models.CharField(max_length=200,verbose_name=_("Designation"))
    #~ text = models.TextField(blank=True,null=True)
    #~ def __unicode__(self):
        #~ return self.name

#~ class StudyContents(reports.Report):
    #~ label = _('Study contents')
    #~ model = StudyContent
    #~ order_by = "name"
    
#~ class StudyContentsByType(StudyContents):
    #~ fk_name = 'type'


class HistoryByPerson(reports.Report):
    def create_instance(self,req,**kw):
        obj = super(HistoryByPerson,self).create_instance(req,**kw)
        if obj.person is not None:
            previous_exps = self.model.objects.filter(person=obj.person).order_by('started')
            if previous_exps.count() > 0:
                exp = previous_exps[previous_exps.count()-1]
                if exp.stopped:
                    obj.started = exp.stopped
                else:
                    obj.started = exp.started
        return obj
    

#
# Study
#


class Study(CountryCity):
    class Meta:
        verbose_name = _("study or education")
        verbose_name_plural = _("Studies & education")
    person = models.ForeignKey("contacts.Person",verbose_name=_("Person"))
    type = models.ForeignKey(StudyType,verbose_name=_("Study type"))
    content = models.CharField(max_length=200,blank=True,null=True,verbose_name=_("Study content"))
    #~ content = models.ForeignKey(StudyContent,blank=True,null=True,verbose_name=_("Study content"))
  
    started = fields.MonthField(_("started"),blank=True,null=True)
    stopped = fields.MonthField(_("stopped"),blank=True,null=True)
    #~ started = models.DateField(blank=True,null=True,verbose_name=_("started"))
    #~ stopped = models.DateField(blank=True,null=True,verbose_name=_("stopped"))
    #~ started = fields.MonthField(blank=True,null=True,verbose_name=_("started"))
    #~ stopped = fields.MonthField(blank=True,null=True,verbose_name=_("stopped"))
    success = models.BooleanField(verbose_name=_("Success"),default=False)
    language = models.ForeignKey("countries.Language",
        blank=True,null=True,verbose_name=_("Language"))
    #~ language = fields.LanguageField(blank=True,null=True,verbose_name=_("Language"))
    
    school = models.CharField(max_length=200,blank=True,null=True,verbose_name=_("School"))
    #~ school = models.ForeignKey("contacts.Company",blank=True,null=True,verbose_name=_("School"))
    
    remarks = models.TextField(blank=True,null=True,verbose_name=_("Remarks"))
    
    def __unicode__(self):
        return unicode(self.type)
  
        
class StudiesByPerson(HistoryByPerson):
    "List of studies for a known person."
    model = Study
    fk_name = 'person'
    #~ label = _("Studies & experiences")
    button_label = _("Studies")
    order_by = ["started"]
    column_names = 'type content started stopped country city success language school remarks *'
    
    
#
# LanguageKnowledge
#

class LanguageKnowledge(models.Model):
    class Meta:
        verbose_name = _("language knowledge")
        verbose_name_plural = _("language knowledges")
        
    person = models.ForeignKey("contacts.Person")
    language = models.ForeignKey("countries.Language",verbose_name=_("Language"))
    #~ language = models.ForeignKey("countries.Language")
    #~ language = fields.LanguageField()
    spoken = HowWell.field(verbose_name=_("spoken"))
    written = HowWell.field(verbose_name=_("written"))
    
    def __unicode__(self):
        if self.language_id is None:
            return ''
        if self.spoken > '1' and self.written > '1':
            return _(u"%s (s/w)") % self.language
        elif self.spoken > '1':
            return _(u"%s (s)") % self.language
        elif self.written > '1':
            return _(u"%s (w)") % self.language
        else:
            return unicode(self.language)
      
    
class LanguageKnowledgesByPerson(reports.Report):
    model = LanguageKnowledge
    fk_name = 'person'
    #~ label = _("Language knowledge")
    #~ button_label = _("Languages")
    column_names = "language spoken written"

# 
# PROPERTIES
# 

from lino.modlib.properties import models as properties

class PersonProperty(properties.PropertyOccurence):
    class Meta:
        app_label = 'properties'
        verbose_name = _("Property")
        verbose_name_plural = _("Properties")
        
    person = models.ForeignKey("contacts.Person")
    remark = models.CharField(max_length=200,
        blank=True,null=True,
        verbose_name=_("Remark"))
  
class PropsByPerson(reports.Report):
    model = PersonProperty
    fk_name = 'person'
    column_names = "property value remark *"
    hidden_columns = frozenset(['group'])
    
    
class PersonPropsByProp(reports.Report):
    model = PersonProperty
    fk_name = 'property'
    column_names = "person value remark *"
    hidden_columns = frozenset(['group'])
    
#~ class PersonPropsByType(reports.Report):
    #~ model = PersonProperty
    #~ fk_name = 'type'
    #~ column_names = "person property value remark *"
    #~ hidden_columns = frozenset(['group'])
    
    
class ConfiguredPropsByPerson(PropsByPerson):
    propgroup_config_name = NotImplementedError
    typo_check = False # to avoid warning "ConfiguredPropsByPerson defines new attribute(s) propgroup_config_name"
    def setup_actions(self):
        if not self.propgroup_config_name is NotImplementedError:
            #~ pg = self.get_configured_action() 
            pg = getattr(settings.LINO.config,self.propgroup_config_name)
            self.known_values = dict(group=pg)
            if pg is None:
                self.label = _("(Site setting %s is empty)" % self.propgroup_config_name)
            else:
                self.label = babelattr(pg,'name')
        PropsByPerson.setup_actions(self)
        
class SkillsByPerson(ConfiguredPropsByPerson):
    propgroup_config_name = 'propgroup_skills'
  
    #~ def get_configured_action(self):
        #~ return settings.LINO.config.propgroup_skills
        
    #~ def setup_actions(self):
        #~ pg = settings.LINO.config.propgroup_skills
        #~ self.known_values = dict(group=pg)
        #~ if pg is None:
            #~ self.label = babelattr(pg,'name')
        #~ else:
            #~ self.label = babelattr(pg,'name')
        #~ PropsByPerson.setup_actions(self)
        
class SoftSkillsByPerson(ConfiguredPropsByPerson):
    propgroup_config_name = 'propgroup_softskills'
    #~ def get_configured_action(self):
        #~ return settings.LINO.config.propgroup_softskills
        
    #~ def setup_actions(self):
        #~ pg = get_site_config().propgroup_softskills
        #~ self.known_values = dict(group=pg)
        #~ self.label = babelattr(pg,'name')
        #~ PropsByPerson.setup_actions(self)
        
class ObstaclesByPerson(ConfiguredPropsByPerson):
    propgroup_config_name = 'propgroup_obstacles'
    #~ def get_configured_action(self):
        #~ return settings.LINO.config.propgroup_obstacles
        
    #~ def setup_actions(self):
        #~ pg = get_site_config().propgroup_obstacles
        #~ self.known_values = dict(group=pg)
        #~ self.label = babelattr(pg,'name')
        #~ PropsByPerson.setup_actions(self)
    
#
# JOBS
#
    
class JobExperience(models.Model):
    class Meta:
        verbose_name = _("job experience")
        verbose_name_plural = _("job experiences")
    person = models.ForeignKey("contacts.Person",verbose_name=_("Person"))
    #~ company = models.ForeignKey("contacts.Company",verbose_name=_("Company"))
    company = models.CharField(max_length=200,verbose_name=_("company"))
    #~ type = models.ForeignKey(JobType,verbose_name=_("job type"))
    title = models.CharField(max_length=200,verbose_name=_("job title"),blank=True)
    country = models.ForeignKey("countries.Country",
        blank=True,null=True,
        verbose_name=_("Country"))
  
    started = fields.MonthField(_("started"),blank=True,null=True)
    stopped = fields.MonthField(_("stopped"),blank=True,null=True)
    
    remarks = models.TextField(blank=True,null=True,verbose_name=_("Remarks"))
    
    def __unicode__(self):
        return unicode(self.title)
  
class JobExperiencesByPerson(HistoryByPerson):
    "List of job experiences for a known person"
    model = JobExperience
    fk_name = 'person'
    order_by = ["started"]
    
  

#
# ACTIVITIY (Berufscode)
#
class Activity(models.Model):
    class Meta:
        verbose_name = _("activity")
        verbose_name_plural = _("activities")
    name = models.CharField(max_length=80)
    lst104 = models.BooleanField(_("Appears in Listing 104"))
    
    def __unicode__(self):
        return unicode(self.name)

class Activities(reports.Report):
    model = Activity
    #~ label = _('Activities')

#~ class ActivitiesByPerson(Activities):
    #~ fk_name = 'activity'

#~ class ActivitiesByCompany(Activities):
    #~ fk_name = 'activity'
    
#
# EXCLUSION TYPES (Sperrgründe)
#
class ExclusionType(models.Model):
    class Meta:
        verbose_name = _("exclusion type")
        verbose_name_plural = _('exclusion types')
        
    name = models.CharField(max_length=200)
    
    def __unicode__(self):
        return unicode(self.name)

class ExclusionTypes(reports.Report):
    model = ExclusionType
    #~ label = _('Exclusion Types')
    
#
# EXCLUSIONS (Arbeitslosengeld-Sperrungen)
#
class Exclusion(models.Model):
    class Meta:
        verbose_name = _("exclusion")
        verbose_name_plural = _('exclusions')
        
    person = models.ForeignKey("contacts.Person")
    type = models.ForeignKey("dsbe.ExclusionType",verbose_name=_("Reason"))
    excluded_from = models.DateField(blank=True,null=True,verbose_name=_("from"))
    excluded_until = models.DateField(blank=True,null=True,verbose_name=_("until"))
    remark = models.CharField(max_length=200,blank=True,verbose_name=_("Remark"))
    
    def __unicode__(self):
        s = unicode(self.type)
        if self.excluded_from: s += ' ' +unicode(self.excluded_from)
        if self.excluded_until: s += '-'+unicode(self.excluded_until)
        return s

class Exclusions(reports.Report):
    model = Exclusion
    #~ label = _('Exclusions')
    
class ExclusionsByPerson(Exclusions):
    fk_name = 'person'
    column_names = 'excluded_from excluded_until type remark'


#
# COACHING TYPES 
#
#~ class CoachingType(models.Model):
    #~ class Meta:
        #~ verbose_name = _("coaching type")
        #~ verbose_name_plural = _('coaching types')
        
    #~ name = models.CharField(max_length=200)
    
    #~ def __unicode__(self):
        #~ return unicode(self.name)

#~ class CoachingTypes(reports.Report):
    #~ model = CoachingType
    
#
# COACHINGS
#
#~ class Coaching(models.Model):
    #~ class Meta:
        #~ verbose_name = _("coaching")
        #~ verbose_name_plural = _('coachings')
    #~ person = models.ForeignKey("contacts.Person",verbose_name=_("Client"))
    #~ coach = models.ForeignKey("auth.User",verbose_name=_("Coach"))
    #~ type = models.ForeignKey("dsbe.CoachingType",verbose_name=_("Coaching type"))
    #~ remark = models.CharField(max_length=200,blank=False,verbose_name=_("Remark"))
    

#~ class Coachings(reports.Report):
    #~ model = Coaching
    
#~ class CoachingsByPerson(Coachings):
    #~ fk_name = 'person'
    #~ column_names = 'coach type remark *'
    #~ label = _('Coaches')

#
# CONTRACT TYPES 
#
class ContractType(mixins.PrintableType):
    templates_group = 'contracts'
    class Meta:
        verbose_name = _("Contract Type")
        verbose_name_plural = _('Contract Types')
        
    ref = models.CharField(_("reference"),max_length=20,blank=True)
    name = babel.BabelCharField(_("contract title"),max_length=200)
    
    def __unicode__(self):
        return unicode(babel.babelattr(self,'name'))
#~ add_babel_field(ContractType,'name')

class ContractTypes(reports.Report):
    model = ContractType
    column_names = 'name build_method template *'

#
# EXAMINATION POLICIES
#
class ExamPolicy(models.Model):
    class Meta:
        verbose_name = _("examination policy")
        verbose_name_plural = _('examination policies')
        
    name = babel.BabelCharField(_("designation"),max_length=200)
    
    def __unicode__(self):
        return unicode(babel.babelattr(self,'name'))
    #~ def __unicode__(self):
        #~ return unicode(self.name)
#~ add_babel_field(ExamPolicy,'name')

class ExamPolicies(reports.Report):
    model = ExamPolicy
    column_names = 'name *'

#
# CONTRACT ENDINGS
#
class ContractEnding(models.Model):
    class Meta:
        verbose_name = _("Contract Ending")
        verbose_name_plural = _('Contract Endings')
        
    name = models.CharField(_("designation"),max_length=200)
    
    def __unicode__(self):
        return unicode(self.name)
        
class ContractEndings(reports.Report):
    model = ContractEnding
    column_names = 'name *'
    order_by = ['name']

#
# COURSE ENDINGS
#
class CourseEnding(models.Model):
    u"""
    Eine Kursbeendigung ist eine *Art und Weise, wie eine Kursanfrage beendet wurde*.
    Später können wir dann Statistiken machen, wieviele Anfragen auf welche Art und 
    Weise beendet wurden.
    """
    class Meta:
        verbose_name = _("Course Ending")
        verbose_name_plural = _('Course Endings')
        
    name = models.CharField(_("designation"),max_length=200)
    
    def __unicode__(self):
        return unicode(self.name)
        
class CourseEndings(reports.Report):
    model = CourseEnding
    column_names = 'name *'
    order_by = ['name']


#
# AID TYPES
#
class AidType(models.Model):
    class Meta:
        verbose_name = _("aid type")
        verbose_name_plural = _('aid types')
        
    name = babel.BabelCharField(_("designation"),max_length=200)
    
    def __unicode__(self):
        return unicode(babel.babelattr(self,'name'))
#~ add_babel_field(AidType,'name')

class AidTypes(reports.Report):
    model = AidType
    column_names = 'name *'



#
# CONTRACTS
#
class Contract(mixins.DiffingMixin,mixins.TypedPrintable,mixins.Reminder,contacts.ContactDocument):
    """
    A Contract
    """
    class Meta:
        verbose_name = _("Contract")
        verbose_name_plural = _('Contracts')
        
    type = models.ForeignKey("dsbe.ContractType",verbose_name=_("contract type"),blank=True)
    
    applies_from = models.DateField(_("applies from"),blank=True,null=True,)
    applies_until = models.DateField(_("applies until"),blank=True,null=True)
    date_decided = models.DateField(blank=True,null=True,verbose_name=_("date decided"))
    date_issued = models.DateField(blank=True,null=True,verbose_name=_("date issued"))
    duration = models.IntegerField(_("duration (days)"),blank=True,null=True,default=None)
    
    
    regime = models.CharField(_("regime"),max_length=200,blank=True,null=True)
    schedule = models.CharField(_("schedule"),max_length=200,blank=True,null=True)
    hourly_rate = fields.PriceField(_("hourly rate"),blank=True,null=True)
    refund_rate = models.CharField(_("refund rate"),max_length=200,
        blank=True,null=True)
    
    reference_person = models.CharField(_("reference person"),max_length=200,
        blank=True,null=True)
    
    responsibilities = fields.RichTextField(_("responsibilities"),blank=True,null=True,format='html')
    
    stages = fields.RichTextField(_("stages"),blank=True,null=True,format='html')
    goals = fields.RichTextField(_("goals"),blank=True,null=True,format='html')
    duties_asd = fields.RichTextField(_("duties ASD"),blank=True,null=True,format='html')
    duties_dsbe = fields.RichTextField(_("duties DSBE"),blank=True,null=True,format='html')
    duties_company = fields.RichTextField(_("duties company"),blank=True,null=True,format='html')
    
    user_asd = models.ForeignKey("users.User",verbose_name=_("responsible (ASD)"),
        related_name='contracts_asd',blank=True,null=True) 
    
    exam_policy = models.ForeignKey("dsbe.ExamPolicy",blank=True,null=True,
        verbose_name=_("examination policy"))
        
    ending = models.ForeignKey("dsbe.ContractEnding",blank=True,null=True,
        verbose_name=_("Ending"))
    date_ended = models.DateField(blank=True,null=True,verbose_name=_("date ended"))
    
    #~ aid_nature = models.CharField(_("aid nature"),max_length=100,blank=True)
    #~ aid_rate = models.CharField(_("aid rate"),max_length=100,blank=True)
    
    @chooser(simple_values=True)
    def duration_choices(cls):
        return [ 312, 468, 624 ]
        #~ return [ 0, 25, 50, 100 ]
    
    @chooser(simple_values=True)
    def regime_choices(cls,language):
        return language_choices(language,REGIME_CHOICES)
    
    @chooser(simple_values=True)
    def schedule_choices(cls,language):
        return language_choices(language,SCHEDULE_CHOICES)
    
    @chooser(simple_values=True)
    def refund_rate_choices(cls):
        return [ 
        u"0%",
        u"25%",
        u"50%",
        u"100%",
        ]
    
    
    def disabled_fields(self,request):
        if self.must_build:
            return []
        return settings.LINO.CONTRACT_PRINTABLE_FIELDS
        
    
    def __unicode__(self):
        msg = _("Contract # %s")
        #~ msg = _("Contract # %(pk)d (%(person)s/%(company)s)")
        #~ return msg % dict(pk=self.pk, person=self.person, company=self.company)
        return msg % self.pk
        
    def get_reminder_html(self,ui,user):
        url = ui.get_detail_url(self,fmt='detail')
        if self.type:
            s = unicode(self.type)
        else:
            s = self._meta.verbose_name
        s += ' #' + unicode(self.pk)
        
        s = ui.href(url,cgi.escape(s))
        
        more = []
        if self.person:
            more.append(ui.href_to(self.person))
        if self.company:
            more.append(ui.href_to(self.company))
        if self.user and self.user != user:
            more.append(cgi.escape(unicode(self.user)))
        if self.reminder_text:
            more.append(cgi.escape(self.reminder_text))
        else:
            more.append(cgi.escape(_('Due date reached')))
        return s + '&nbsp;: ' + (', '.join(more))
        
    def summary_row(self,ui,rr,**kw):
        s = ''
        if self.reminder_text:
            s += '<b>' + cgi.escape(self.reminder_text) + '</b> '
        s += ui.href_to(self)
        if self.person:
            if self.company:
                s += "(" + ui.href_to(self.person) + "/" + ui.href_to(self.company) + ")"
            else:
                s += "(" + ui.href_to(self.person) + ")"
        elif self.company:
            s += "(" + ui.href_to(self.company) + ")"
        return s
        
    def dsbe_person(self):
        if self.person_id is not None:
            if self.person.coach2_id is not None:
                return self.person.coach2_id
            return self.person.coach1 or self.user
            
        #~ try:
            #~ return self.person.coaching_set.get(type__name__exact='DSBE').coach        
        #~ except Exception,e:
            #~ return self.person.user or self.user
            
    def on_person_changed(self,request):
        if self.person_id is not None:
            if self.person.coach1_id is None or self.person.coach1_id == self.user_id:
                self.user_asd = None
            else:
                self.user_asd = self.person.coach1
                
    def on_create(self,request):
        super(Contract,self).on_create(request)
        self.on_person_changed(request)
      
    def full_clean(self):
      
        if self.person_id is not None:
            #~ if not self.user_asd:
                #~ if self.person.user != self.user:
                    #~ self.user_asd = self.person.user
            if self.person.birth_date and self.applies_from:
                def duration(refdate):
                    delta = refdate - self.person.birth_date
                    age = delta.days / 365
                    if age < 36:
                        return 312
                    elif age < 50:
                        return 468
                    else:
                        return 624
              
                if self.duration is None:
                    if self.applies_until:
                        self.duration = duration(self.applies_until)
                    else:
                        self.duration = duration(self.applies_from)
                        self.applies_until = self.applies_from + datetime.timedelta(days=self.duration)
                    
        if self.company is not None:
          
            if self.hourly_rate is None:
                self.hourly_rate = self.company.hourly_rate
                
            if self.type_id is None \
                and self.company.type is not None \
                and self.company.type.contract_type is not None:
                self.type = self.company.type.contract_type
    @classmethod
    def site_setup(cls,lino):
        """
        Here's how to override the default verbose_name of a field
        """
        resolve_field('dsbe.Contract.user').verbose_name=_("responsible (DSBE)")
        lino.CONTRACT_PRINTABLE_FIELDS = reports.fields_list(cls,
            'person company contact type '
            'applies_from applies_until duration '
            'language schedule regime hourly_rate refund_rate reference_person '
            'stages duties_dsbe duties_company duties_asd '
            'user user_asd exam_policy '
            'date_decided date_issued responsibilities')


class Contracts(reports.Report):
    model = Contract
    column_names = 'id company applies_from applies_until user type *'
    order_by = ['id']
    
class ContractsByPerson(Contracts):
    fk_name = 'person'
    column_names = 'company applies_from applies_until user type *'

        
class ContractsByCompany(Contracts):
    fk_name = 'company'
    column_names = 'person applies_from applies_until user type *'

class ContractsByType(Contracts):
    fk_name = 'type'
    column_names = "applies_from person company user *"
    order_by = ["applies_from"]

class MyContracts(mixins.ByUser,Contracts):
    column_names = "applies_from person company *"
    label = _("My contracts")
    #~ order_by = "reminder_date"
    #~ column_names = "reminder_date person company *"
    order_by = ["applies_from"]
    #~ filter = dict(reminder_date__isnull=False)


#
# NOTES
#
class Note(notes.Note,contacts.PartnerDocument):
    class Meta:
        app_label = 'notes'
        verbose_name = _("Event/Note") # application-specific override
        verbose_name_plural = _("Events/Notes")

    def get_reminder_html(self,ui,user):
        url = ui.get_detail_url(self,fmt='detail')
        if self.type:
            s = unicode(self.type)
        else:
            s = self._meta.verbose_name
        s += ' #' + unicode(self.pk)
        
        s = ui.href(url,cgi.escape(s))
        
        more = []
        if self.person:
            more.append(ui.href_to(self.person))
        if self.company:
            more.append(ui.href_to(self.company))
        if self.event_type:
            more.append(cgi.escape(unicode(self.event_type)))
        if self.subject:
            more.append(cgi.escape(self.subject))
        if self.user and self.user != user:
            more.append(cgi.escape(unicode(self.user)))
        more.append(babel.dtos(self.date))
        if self.reminder_text:
            more.append(cgi.escape(self.reminder_text))
        else:
            more.append(cgi.escape(_('Due date reached')))
        return s + '&nbsp;: ' + (', '.join(more))
        
    @classmethod
    def site_setup(cls,lino):
        lino.NOTE_PRINTABLE_FIELDS = reports.fields_list(cls,
        '''date subject body language person company type event_type''')
        
        
    #~ def disabled_fields(self,request):
        #~ if self.must_build:
            #~ return []
        #~ return NOTE_PRINTABLE_FIELDS
        
#~ NOTE_PRINTABLE_FIELDS = reports.fields_list(Note,
    #~ '''date subject body language person company''')
    
class NotesByPerson(notes.Notes):
    fk_name = 'person'
    #~ column_names = "date type event_type subject body_html user company *"
    column_names = "date type event_type subject body user company *"
    order_by = ["date"]
  
class NotesByCompany(notes.Notes):
    fk_name = 'company'
    #~ column_names = "date type event_type subject body_html user person *"
    column_names = "date type event_type subject body user person *"
    order_by = ["date"]
    
class MyNotes(notes.MyNotes):
    #~ fk_name = 'user'
    #~ column_names = "date type event_type subject person company body_html *"
    column_names = "date type event_type subject person company body *"
    
  
#
# LINKS
#
class Link(links.Link,contacts.PartnerDocument):
    class Meta:
        app_label = 'links'

class LinksByPerson(links.LinksByOwnerBase):
    fk_name = 'person'
    column_names = "name url user date company *"
    order_by = ["date"]
  
class LinksByCompany(links.LinksByOwnerBase):
    fk_name = 'company'
    column_names = "name url user date person *"
    order_by = ["date"]
    

#
# COURSES
#


#~ class CourseProvider(models.Model):
class CourseProvider(Company):
    """Kursanbieter (KAP, Oikos, Lupe, ...) 
    """
    class Meta:
        app_label = 'dsbe'
    #~ name = models.CharField(max_length=200,
          #~ verbose_name=_("Name"))
    #~ company = models.ForeignKey("contacts.Company",blank=True,null=True,verbose_name=_("Company"))
    
#~ CourseProvider = Company

class CourseProviders(Companies):
    """
    List of Companies that have `Company.is_courseprovider` activated.
    """
    use_as_default_report = False
    #~ app_label = 'dsbe'
    label = _("Course providers")
    model = CourseProvider
    #~ known_values = dict(is_courseprovider=True)
    #~ filter = dict(is_courseprovider__exact=True)
    
    #~ def create_instance(self,req,**kw):
        #~ instance = super(CourseProviders,self).create_instance(req,**kw)
        #~ instance.is_courseprovider = True
        #~ return instance
  
class CourseContent(models.Model):
    u"""
    Ein Kursinhalt (z.B. "Französisch", "Deutsch", "Alphabétisation",...)
    """
    
    class Meta:
        verbose_name = _("Course Content")
        verbose_name_plural = _('Course Contents')
        
    name = models.CharField(max_length=200,
          blank=True,null=True,
          verbose_name=_("Name"))
    u"""
    Bezeichnung des Kursinhalts (nach Konvention des DSBE).
    """
          
    def __unicode__(self):
        return unicode(self.name)
        
  
class Course(models.Model):
    """
    Ein konkreter Kurs, der an einem bestimmten Datum beginnt 
    und bei einem bestimmten 
    :class:`Kursanbieter <CourseProvider>` stattfindet
    (und für den ihr Kandidaten zu vermitteln plant).
    """
    class Meta:
        verbose_name = _("Course")
        verbose_name_plural = _('Courses')
        
    title = models.CharField(max_length=200,
        verbose_name=_("Name"))
    u"""
    Der Titel des Kurses. Maximal 200 Zeichen.
    """
    
    content = models.ForeignKey("dsbe.CourseContent",
        verbose_name=_("Course content"))
    """
    Der Inhalt des Kurses (ein :class:`CourseContent`)
    """
    
    provider = models.ForeignKey(CourseProvider,
        verbose_name=_("Course provider"))
    """
    Der Kursanbieter (eine :class:`Company`)
    """
    
    @chooser()
    def provider_choices(cls):
        return CourseProviders.request().queryset
        
    start_date = models.DateField(_("start date"),blank=True,null=True)
    """
    Datum, wann der Kurs beginnt. 
    """
    
    #~ content = models.ForeignKey("dsbe.CourseContent",verbose_name=_("Course content"))
  
    remark = models.CharField(max_length=200,
        blank=True,null=True,
        verbose_name=_("Remark"))
    u"""
    Bemerkung über diesen konkreten Kurs. Maximal 200 Zeichen.
    """
        
    def __unicode__(self):
        if self.start_date is None:
            return u'%s %s' % (self.title,self.provider)
        return u'%s %s %s' % (self.title,self.start_date,self.provider)
  
    @classmethod
    def setup_report(model,rpt):
        rpt.add_action(DirectPrintAction('candidates',_("List of candidates"),'courses/candidates.odt'))
        rpt.add_action(DirectPrintAction('participants',_("List of participants"),'courses/participants.odt'))
        
    def get_print_language(self,pm):
        "Used by DirectPrintAction"
        return DEFAULT_LANGUAGE
        
    def participants(self):
        u"""
        Liste von :class:`CourseRequest`-Instanzen, 
        die in diesem Kurs eingetragen sind. 
        """
        return ParticipantsByCourse().request(master_instance=self)
        
    def candidates(self):
        u"""
        Liste von :class:`CourseRequest`-Instanzen, 
        die noch in keinem Kurs eingetragen sind, aber für diesen Kurs in Frage 
        kommen. 
        """
        return CandidatesByCourse().request(master_instance=self)
        
        
#~ class CourseRequest(mixins.Reminder):
class CourseRequest(models.Model):
    u"""
    A Course Request is created when a certain Person expresses her 
    wish to participate in a Course with a certain CourseContent.
    """
    class Meta:
        verbose_name = _("Course Requests")
        verbose_name_plural = _('Course Requests')
        
    person = models.ForeignKey("contacts.Person",
        verbose_name=_("Person"))
    u"Die Person (ein Objekt vom Typ :class:`Person`.)"
    
    content = models.ForeignKey("dsbe.CourseContent",
        verbose_name=_("Course content"))
    u"Der gewünschte Kursinhalt (ein Objekt vom Typ :class:`CourseConent`.)"
    
    date_submitted = models.DateField(_("date submitted"),auto_now_add=True)
    u"Das Datum, an dem die Anfrage erstellt wurde."
    
    #~ """Empty means 'any provider'
    #~ """
    #~ provider = models.ForeignKey(CourseProvider,blank=True,null=True,
        #~ verbose_name=_("Course provider"))
        
    #~ @chooser()
    #~ def provider_choices(cls):
        #~ return CourseProviders.request().queryset
        
    course = models.ForeignKey("dsbe.Course",blank=True,null=True,
        verbose_name=_("Course found"))
    u"""
    Der Kurs, durch den diese Anfrage befriedigt wurde 
    (ein Objekt vom Typ :class:`lino.apps.dsbe.models.Course`).
    So lange dieses Feld leer ist, gilt die Anfrage als offen.
    """
        
    #~ """
    #~ The person's feedback about how satisfied she was.
    #~ """
    #~ satisfied = StrengthField(verbose_name=_("Satisfied"),blank=True,null=True)
    
    #~ remark = models.CharField(max_length=200,
    remark = models.TextField(
        blank=True,null=True,
        verbose_name=_("Remark"))
    u"""
    Bemerkung zu dieser konkreten Kursanfrage oder -teilnahme.
    """
        
    date_ended = models.DateField(blank=True,null=True,verbose_name=_("date ended"))
    u"""
    Datum der effektives Beendigung dieser Kursteilname.
    """
    
    ending = models.ForeignKey("dsbe.CourseEnding",blank=True,null=True,
        verbose_name=_("Ending"))
    u"""
    Die Art der Beendigung 
    (ein Objekt vom Typ :class:`CourseEnding`.)
    Das wird benutzt für spätere Statistiken.
    """
    
        
class Courses(reports.Report):
    model = Course
    order_by = ['start_date']

class CourseContents(reports.Report):
    model = CourseContent
    order_by = ['name']

class CoursesByProvider(Courses):
    fk_name = 'provider'

class CourseRequests(reports.Report):
    model = CourseRequest
    order_by = ['date_submitted']

class CourseRequestsByPerson(CourseRequests):
    fk_name = 'person'
    column_names = '* id'

class RequestsByCourse(CourseRequests):
    fk_name = 'course'
  
    def create_instance(self,req,**kw):
        obj = super(RequestsByCourse,self).create_instance(req,**kw)
        if obj.course is not None:
            obj.content = obj.course.content
        return obj
    
class ParticipantsByCourse(RequestsByCourse):
    label = _("Participants")
    column_names = 'person remark date_ended ending'
    
    def setup_actions(self):
        class Unregister(reports.RowAction):
            label = _("Unregister")
            def run(self,rr,elem):
                course = elem.course
                elem.course = None
                elem.save()
                return rr.ui.success_response(refresh_all=True,
                  message=_("%(person)s has been unregistered from %(course)s") % dict(person=elem.person,course=course))
        self.add_action(Unregister())

class CandidatesByCourse(RequestsByCourse):
    label = _("Candidates")
    column_names = 'person remark content date_submitted'
    #~ can_add = perms.never
    
    def get_request_queryset(self,rr):
        if rr.master_instance is None:
            return []
        return self.model.objects.filter(course__isnull=True,
            content__exact=rr.master_instance.content)
    
    def setup_actions(self):
        class Register(reports.RowAction):
            label = _("Register")
            def run(self,rr,elem):
                elem.course = rr.master_instance
                elem.save()
                return rr.ui.success_response(refresh_all=True,
                  message=_("%(person)s has been registered to %(course)s") % dict(
                      person=elem.person,course=elem.course))
        self.add_action(Register())
    
    def create_instance(self,req,**kw):
        """Manually clear the `course` field.
        """
        obj = super(CandidatesByCourse,self).create_instance(req,**kw)
        obj.course = None
        return obj

#
# SEARCH
#
class PersonSearch(mixins.AutoUser):
    class Meta:
        verbose_name = _("Person Search")
        verbose_name_plural = _('Person Searches')
        
    title = models.CharField(max_length=200,verbose_name=_("Search Title"))
    aged_from = models.IntegerField(_("Aged from"),
        blank=True,null=True)
    aged_to = models.IntegerField(_("Aged to"),
        blank=True,null=True)
    sex = models.CharField(max_length=1,blank=True,null=True,
        verbose_name=_("Sex"),
        choices=SEX_CHOICES) 
        
    only_my_persons = models.BooleanField(verbose_name=_("Only my persons")) # ,default=True)
    
    coached_by = models.ForeignKey("users.User",
        verbose_name=_("Coached by"),
        related_name='persons_coached',
        blank=True,null=True)
    period_from = models.DateField(
        blank=True,null=True,
        verbose_name=_("Period from"))
    period_until = models.DateField(
        blank=True,null=True,
        verbose_name=_("until"))
    
    def result(self):
        for p in PersonsBySearch().request(master_instance=self):
            yield p
        
    def __unicode__(self):
        return self._meta.verbose_name + ' "%s"' % (self.title or _("Unnamed"))
        
    def get_print_language(self,pm):
        return DEFAULT_LANGUAGE
        
    @classmethod
    def setup_report(model,rpt):
        rpt.add_action(DirectPrintAction('suchliste',_("Drucken"),'persons/suchliste.odt'))
        
class MySearches(mixins.ByUser):
    model = PersonSearch
    
class WantedLanguageKnowledge(models.Model):
    search = models.ForeignKey(PersonSearch)
    language = models.ForeignKey("countries.Language",verbose_name=_("Language"))
    spoken = HowWell.field(verbose_name=_("spoken"))
    written = HowWell.field(verbose_name=_("written"))

class WantedSkill(properties.PropertyOccurence):
    class Meta:
        app_label = 'properties'
        verbose_name = _("Wanted property")
        verbose_name_plural = _("Wanted properties")
        
    search = models.ForeignKey(PersonSearch)
    
class UnwantedSkill(properties.PropertyOccurence):
    class Meta:
        app_label = 'properties'
        verbose_name = _("Unwanted property")
        verbose_name_plural = _("Unwanted properties")
    search = models.ForeignKey(PersonSearch)
    
    
class LanguageKnowledgesBySearch(reports.Report):
    label = _("Wanted language knowledges")
    fk_name = 'search'
    model = WantedLanguageKnowledge

class WantedPropsBySearch(reports.Report):
    label = _("Wanted properties")
    fk_name = 'search'
    model = WantedSkill

class UnwantedPropsBySearch(reports.Report):
    label = _("Unwanted properties")
    fk_name = 'search'
    model = UnwantedSkill

class PersonSearches(reports.Report):
    model = PersonSearch
    
class PersonsBySearch(reports.Report):
    """
    This is the slave report of a PersonSearch that shows the 
    Persons matching the search criteria. 
    
    Note that this is a slave report without a :attr:`fk_name <lino.reports.Report.fk_name>`.
    """
  
    model = Person
    master = PersonSearch
    app_label = 'dsbe'
    label = _("Found persons")
    
    can_add = perms.never
    can_change = perms.never
    
    def get_request_queryset(self,rr):
        """
        Here is the code that builds the query. It can be quite complex.
        See :srcref:`/lino/modlib/dsbe/models.py` (search this file for "PersonsBySearch").
        """
        search = rr.master_instance
        if search is None:
            return []
        kw = {}
        qs = self.model.objects.order_by('name')
        today = datetime.date.today()
        if search.sex:
            qs = qs.filter(sex__exact=search.sex)
        if search.aged_from:
            #~ q1 = models.Q(birth_date__isnull=True)
            #~ q2 = models.Q(birth_date__gte=today-datetime.timedelta(days=search.aged_from*365))
            #~ qs = qs.filter(q1|q2)
            qs = qs.filter(birth_date__lte=today-datetime.timedelta(days=search.aged_from*365))
        if search.aged_to:
            #~ q1 = models.Q(birth_date__isnull=True)
            #~ q2 = models.Q(birth_date__lte=today-datetime.timedelta(days=search.aged_to*365))
            #~ qs = qs.filter(q1|q2)
            qs = qs.filter(birth_date__gte=today-datetime.timedelta(days=search.aged_to*365))
            
        if search.only_my_persons:
            qs = only_my_persons(qs,search.user)
        
        if search.coached_by:
            qs = only_my_persons(qs,search.coached_by)
            
        qs = only_coached_persons(qs,search.period_from,search.period_until)
          
        required_id_sets = []
        
        required_lk = [lk for lk in search.wantedlanguageknowledge_set.all()]
        if required_lk:
            # language requirements are OR'ed
            ids = set()
            for rlk in required_lk:
                fkw = dict(language__exact=rlk.language)
                if rlk.spoken is not None:
                    fkw.update(spoken__gte=rlk.spoken)
                if rlk.written is not None:
                    fkw.update(written__gte=rlk.written)
                q = LanguageKnowledge.objects.filter(**fkw)
                ids.update(q.values_list('person__id',flat=True))
            required_id_sets.append(ids)
            
        rprops = [x for x in search.wantedskill_set.all()]
        if rprops: # required properties
            ids = set()
            for rp in rprops:
                fkw = dict(property__exact=rp.property) # filter keywords
                if rp.value:
                    fkw.update(value__gte=rp.value)
                q = PersonProperty.objects.filter(**fkw)
                ids.update(q.values_list('person__id',flat=True))
            required_id_sets.append(ids)
          
            
        if required_id_sets:
            s = set(required_id_sets[0])
            for i in required_id_sets[1:]:
                s.intersection_update(i)
                # keep only elements found in both s and i.
            qs = qs.filter(id__in=s)
              
        return qs
    
    

"""
Here we add a new field `contract_type` to the 
standard model CompanyType.
http://osdir.com/ml/django-users/2009-11/msg00696.html
"""
from lino.modlib.contacts.models import CompanyType
CompanyType.add_to_class('contract_type',
    models.ForeignKey("dsbe.ContractType",
        blank=True,null=True,
        verbose_name=_("contract type")))


from lino.models import SiteConfig
reports.inject_field(SiteConfig,
    'job_office',
    models.ForeignKey("contacts.Company",
        blank=True,null=True,
        verbose_name=_("Local job office"),
        related_name='job_office_sites'),
    """The Company whose contact persons will be 
    choices for `Person.job_office_contact`.
    """)
    
reports.inject_field(SiteConfig,
    'propgroup_skills',
    models.ForeignKey('properties.PropGroup',
        blank=True,null=True,
        verbose_name=_("Skills Property Group"),
        related_name='skills_sites'),
    """The property group to be used as master 
    for the SkillsByPerson report.""")
reports.inject_field(SiteConfig,
    'propgroup_softskills',
    models.ForeignKey('properties.PropGroup',
        blank=True,null=True,
        verbose_name=_("Soft Skills Property Group"),
        related_name='softskills_sites',
        ),
    """The property group to be used as master 
    for the SoftSkillsByPerson report."""
    )
reports.inject_field(SiteConfig,
    'propgroup_obstacles',
    models.ForeignKey('properties.PropGroup',
        blank=True,null=True,
        verbose_name=_("Obstacles Property Group"),
        related_name='obstacles_sites',
        ),
    """The property group to be used as master 
    for the ObstaclesByPerson report."""
    )

reports.inject_field(SiteConfig,
    'residence_permit_upload_type',
    #~ UploadType.objects.get(pk=2)
    models.ForeignKey("uploads.UploadType",
        blank=True,null=True,
        verbose_name=_("Upload Type for residence permit"),
        related_name='residence_permit_sites'),
    """The UploadType for `Person.residence_permit`.
    """)
    
reports.inject_field(SiteConfig,
    'work_permit_upload_type',
    #~ UploadType.objects.get(pk=2)
    models.ForeignKey("uploads.UploadType",
        blank=True,null=True,
        verbose_name=_("Upload Type for work permit"),
        related_name='work_permit_sites'),
    """The UploadType for `Person.work_permit`.
    """)

reports.inject_field(SiteConfig,
    'driving_licence_upload_type',
    #~ UploadType.objects.get(pk=2)
    models.ForeignKey("uploads.UploadType",
        blank=True,null=True,
        verbose_name=_("Upload Type for driving licence"),
        related_name='driving_licence_sites'),
    """The UploadType for `Person.driving_licence`.
    """)



"""
...
"""
from lino.tools import resolve_model
User = resolve_model('users.User')
User.grid_search_field = 'username'


"""
Here is how we install case-insensitive sorting in sqlite3.
Note that this caused noticeable performance degradation...

Thanks to 
- http://efreedom.com/Question/1-3763838/Sort-Order-SQLite3-Umlauts
- http://docs.python.org/library/sqlite3.html#sqlite3.Connection.create_collation
- http://www.sqlite.org/lang_createindex.html
"""
from django.db.backends.signals import connection_created

def belgian(s):
  
    s = s.decode('utf-8').lower()
    
    s = s.replace(u'ä',u'a')
    s = s.replace(u'à',u'a')
    s = s.replace(u'â',u'a')
    
    s = s.replace(u'ç',u'c')
    
    s = s.replace(u'é',u'e')
    s = s.replace(u'è',u'e')
    s = s.replace(u'ê',u'e')
    s = s.replace(u'ë',u'e')
    
    s = s.replace(u'ö',u'o')
    s = s.replace(u'õ',u'o')
    s = s.replace(u'ô',u'o')
    
    s = s.replace(u'ß',u'ss')
    
    s = s.replace(u'ù',u'u')
    s = s.replace(u'ü',u'u')
    s = s.replace(u'û',u'u')
    
    return s
    
def stricmp(str1, str2):
    return cmp(belgian(str1),belgian(str2))
    
def my_callback(sender,**kw):
    from django.db.backends.sqlite3.base import DatabaseWrapper
    if sender is DatabaseWrapper:
        db = kw['connection']
        db.connection.create_collation('BINARY', stricmp)

connection_created.connect(my_callback)



