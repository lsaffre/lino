## Copyright 2003-2009 Luc Saffre

## This file is part of the Lino project.

## Lino is free software; you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.

## Lino is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
## or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
## License for more details.

## You should have received a copy of the GNU General Public License
## along with Lino; if not, write to the Free Software Foundation,
## Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import traceback

from django.db import models
from django import forms
from django.conf.urls.defaults import patterns, url, include
from django.forms.models import modelform_factory
from django.forms.models import _get_foreign_key
from django.contrib.auth.decorators import login_required

from lino.django.utils import layouts, render, perms
from lino.django.utils.editing import is_editing

from django.http import HttpResponse
#from django.core import serializers
#from django.shortcuts import render_to_response
#from django.utils import simplejson
from django.utils.safestring import mark_safe

# maps Django field types to a tuple of default paramenters
# each tuple contains: minWidth, maxWidth, is_filter
WIDTHS = {
    models.IntegerField : (2,10,False),
    models.CharField : (10,50,True),
    models.TextField :  (10,50,True),
    models.BooleanField : (10,10,True),
    models.ForeignKey : (5,40,False),
    models.AutoField : (2,10,False),
}


def base_attrs(cl):
    #~ if cl is Report or len(cl.__bases__) == 0:
        #~ return
    #~ myattrs = set(cl.__dict__.keys())
    for b in cl.__bases__:
        for k in base_attrs(b):
            yield k
        for k in b.__dict__.keys():
            yield k
            
            



class ReportParameterForm(forms.Form):
    #~ pgn = forms.IntegerField(required=False,label="Page number") 
    #~ pgl = forms.IntegerField(required=False,label="Rows per page")
    flt = forms.CharField(required=False,label="Text filter")
    #~ fmt = forms.ChoiceField(required=False,label="Format",choices=(
      #~ ( 'form', "editable form" ),
      #~ ( 'show', "read-only display" ),
      #~ ( 'text', "plain text" ),
    #~ ))
    

#        
#  Report
#        

#~ _report_classes = {}

#~ def get_report(name):
    #~ return _report_classes[name]
    
#~ def get_reports():
    #~ return _report_classes
    
model_reports = {}
#_slave_reports = {}
#_reports = []

def register_report_class(rptclass):
    #_reports.append(cls)
    if rptclass.model is None:
        #print "%s : model is None" % rptclass.__name__
        return
    if rptclass.master is None:
        #print "%s : master is None" % rptclass.__name__
        return
    slaves = getattr(rptclass.master,"_lino_slaves",None)
    if slaves is None:
        slaves = {}
        setattr(rptclass.master,'_lino_slaves',slaves)
    slaves[rptclass.__name__] = rptclass
    print "%s : slave for %s" % (rptclass.__name__, rptclass.master.__name__)
    #~ l = _slave_reports.get(rptclass.model,None)
    #~ if l is None:
        #~ l = []
        #~ _slave_reports[rptclass.model] = l
    #~ l.append(rptclass)
    


def register_report(rpt):
    if rpt.model is None:
        return
    if rpt.master is not None:
        return
    if rpt.exclude is not None:
        return
    if rpt.filter is not None:
        return
    db_table = rpt.model._meta.db_table
    if model_reports.has_key(db_table):
        print "[Warning] Ignoring %s" % rpt #.__name__
        return
    model_reports[db_table] = rpt
    
    
def analyse_models():
    """
    - Each model can receive a number of "slaves". 
      slaves are reports that display detail data for a known instance of that model (their master).
      They are stored in a dictionary called '_lino_slaves'.
      
    - For each model we want to find out the "model report", 
      This will be used when displaying a single object. 
      And the "choices report" for a foreignkey field is also currently simply the pointed model's
      model_report.
      `_lino_model_report`

    
    """
    pass
    #~ for model in models.get_models():
        #~ model._lino_slaves = {}
        #~ model._lino_model_report = None
        #~ for rc in reports.report_classes:
            #~ ...
            #~ model._lino_slaves[rpt.name] = rpt
    
#~ def slave_reports(model):
    #~ d = getattr(model,"_lino_slaves",{})
    #~ for b in model.__bases__:
        #~ l += getattr(b,"_lino_slaves",[])
    #~ return l
    #return _slave_reports.get(model,[])

def get_slave(model,name):
    d = getattr(model,"_lino_slaves",{})
    #print d
    if d.has_key(name): return d[name]
    for b in model.__bases__:
        d = getattr(b,"_lino_slaves",{})
        if d.has_key(name): return d[name]
    return None
    
def get_combo_report(model):
    rpt = getattr(model,'_lino_combo',None)
    if rpt: return rpt
    rpt = model_reports[model._meta.db_table]
    model._lino_combo = rpt.__class__(columnNames=rpt.display_field,url=rpt.url) # "__unicode__")
    return model._lino_combo

class ReportMetaClass(type):
    def __new__(meta, classname, bases, classDict):
        cls = type.__new__(meta, classname, bases, classDict)
        if classname != 'Report':
            if cls.typo_check:
                myattrs = set(cls.__dict__.keys())
                for attr in base_attrs(cls):
                    myattrs.discard(attr)
                if len(myattrs):
                    print "[Warning]: %s defines new attribute(s) %s" % (cls,",".join(myattrs))
            register_report_class(cls)
        return cls




class Report:
    __metaclass__ = ReportMetaClass
    queryset = None 
    model = None
    order_by = None
    filter = None
    exclude = None
    title = None
    columnNames = None
    row_layout_class = None
    label = None
    param_form = ReportParameterForm
    #default_filter = ''
    name = None
    form_class = None
    master = None
    fk_name = None
    help_url = None
    master_instance = None
    page_length = 10
    display_field = '__unicode__'
    
    _page_layouts = None
    page_layouts = (layouts.PageLayout ,)
    
    can_view = perms.always
    can_add = perms.is_authenticated
    can_change = perms.is_authenticated

    typo_check = True
    url = None
    #_slaves = None
    
    def __init__(self,**kw):
        for k,v in kw.items():
            if hasattr(self,k):
                setattr(self,k,v)
            else:
                print "[Warning] Ignoring attribute %s" % k
            
        #self._inlines = self.inlines()
        
        if self.model is None:
            self.model = self.queryset.model
        if self.label is None:
            self.label = self.__class__.__name__
        if self.name is None:
            self.name = self.label #.lower()
            
        if self.form_class is None:
            self.form_class = modelform_factory(self.model)
        if self.row_layout_class is None:
            self.row_layout = layouts.RowLayout(self,self.columnNames)
        else:
            assert self.columnNames is None
            self.row_layout = self.row_layout_class(self)
        if self.master:
            self.fk = _get_foreign_key(self.master,
              self.model,self.fk_name)
            #self.name = self.fk.rel.related_name
        if len(self.page_layouts) == 1:
            self.page_layout = self.page_layouts[0](self)
        else:
            self.page_layout = layouts.TabbedPageLayout(self,
              self.page_layouts)
        #~ self._page_layouts = [
              #~ layout(self) for layout in self.page_layouts]
        
        #~ self.ext_row_fields = list(self.row_layout.leaves())
        #~ self.ext_store_fields = self.ext_row_fields
        #~ #if not self.model._meta.pk.attname in self.ext_store_fields:
        #~ if True: # TODO: check whether pk already present...
            #~ self.pk = layouts.FieldElement(None,self.model._meta.pk)
            #~ self.ext_store_fields.append(self.pk)
        #~ if not self.display_field in self.ext_store_fields:
            #~ self.ext_store_fields.append(self.display_field)

            
            
        register_report(self)
        
       
          
        #~ if hasattr(self.model,'slaves'):
            #~ #self.slaves = [ rpt(name=k) for k,v in self.model.slaves().items() ]
        #~ else:
            #~ self.slaves = []
                
    #~ def get_model(self):
        #~ assert self.queryset is not None,"""
        #~ if you set neither model nor queryset in your Report, 
        #~ then you must override get_model(). Example: journals.DocumentsByJournal
        #~ """
        #~ return self.queryset.model
        
    #~ def get_label(self):
        #~ return self.__class__.__name__
        
    def get_slave(self,name):
        return get_slave(self.model,name)
        #l = self.slaves() # to populate
        #return self._slaves.get(name,None)
        
        
    #~ def slaves(self):
        #~ hier: und zwar die slaves in diesem report (nicht alle slaves des modells)
      
        #~ if self._slaves is None:
            #~ self._slaves = {}
            #~ for cl in slave_reports(self.model):
                #~ rpt = cl()
                #~ self._slaves[rpt.name] = rpt
            #print "reports.Report.slaves()", self.__class__.__name__, ":", self._slaves
        #~ return self._slaves.values()
        
        
    #~ def inlines(self):
        #~ return {}
         
    def unused_json_url(self):
        if self.url:
            return "%s/json" % self.url
        if self.master is not None:
            model_name = self.master._meta.object_name.lower()
            app_label = self.master._meta.app_label
            return "/slave/%s/%s/%s" % (app_label,model_name,self.name)
        print self.name, "has neither url nor master!?"
            #~ m = self.master.get(master_id)
            #~ url = render.get_instance_url(m)
            #~ return url+"/"+self.name+"/json"
        
        
    def column_headers(self):
        for e in self.row_layout._main.elements:
            yield e.label
            
    #~ def columns(self):
        #~ return self.row_layout.leaves()
        
    def unused_ext_columns(self):
      try:
        s = set(self.row_layout._main.columns())
        for l in self._page_layouts:
            s.update(l._main.columns())
        return s
        #return self.row_layout._main.columns()
      except Exception,e:
        import traceback
        traceback.print_exc(e)
    
    def get_title(self,renderer):
        #~ if self.title is None:
            #~ return self.label
        return self.title or self.label
        
    #~ def get_master_instance(self):
        #~ raise NotImplementedError
        
    def get_queryset(self,master_instance=None,flt=None):
        if self.queryset is not None:
            qs = self.queryset
        else:
            qs = self.model.objects.all()
        #~ if self.master:
            #~ fk = _get_foreign_key(self.master,self.model,self.fk_name)
            #~ self.fk.get_attname()
        if self.master is None:
            assert master_instance is None
        else:
            if master_instance is None:
                master_instance = self.master_instance
            #print qs
            #print qs.model
            qs = qs.filter(**{self.fk.name:master_instance})
            #~ if self.fk.limit_choices_to:
                #~ qs = qs.filter(**self.fk.limit_choices_to)

        if self.order_by:
            qs = qs.order_by(*self.order_by.split())
        if self.filter:
            qs = qs.filter(**self.filter)
        if self.exclude:
            qs = qs.exclude(**self.exclude)
        if flt is not None:
            l = []
            q = models.Q()
            for field in self.model._meta.fields:
                if isinstance(field,models.CharField):
                    q = q | models.Q(**{
                      field.name+"__contains": flt})
            qs = qs.filter(q)
        return qs
        
    def getLabel(self):
        return self.label
        
    def get_absolute_url(self,root,master_instance=None,**kw):
        # root :  'one' or 'many'
        app_label = self.model._meta.app_label
        if master_instance is None:
            master_instance = self.master_instance
        if master_instance is not None:
            kw['master'] == master_instance.pk
        url = '/%s/%s/%s' % (root,app_label,self.__class__.__name__)
        if len(kw):
            url += urlencode(kw)
        return url
        
    
    #~ def get_row_print_template(self,instance):
        #~ return instance._meta.db_table + "_print.html"
        
    #~ def page_layout(self,i=0):
        #~ if self._page_layouts is None:
            #~ self._page_layouts = [ 
              #~ l(self.model) for l in self.page_layouts]
        #~ return self._page_layouts[i]

    #~ def can_view(self,request,row=None):
        #~ return True
        
    #~ def can_add(self,request,row=None):
        #~ return True
        
    #~ def can_change(self,request,row=None):
        #~ return request.user.is_authenticated()
        
        
    #~ def __unicode__(self):
        #~ #return unicode(self.as_text())
        #~ return unicode("%d row(s)" % self.queryset.count())
    
    def get_urls(self,name):
        if self.url:
            raise RuntimError("Report.get_urls() called again.")
        self.url = "/" + name
        l = []
        l.append(url(r'^%s/(\d+)$' % name, self.view_one))
        #l.append(url(r'^%s/(\d+)/(.+)$' % name, self.view_one_slave))
        l.append(url(r'^%s$' % name, self.view_many))
        l.append(url(r'^%s/(\d+)/pdf$' % name, self.pdf_one))
        l.append(url(r'^%s/pdf$' % name, self.pdf_many))
        #l.append(url(r'^%s/flexigrid$' % name, self.flexigrid))
        l.append(url(r'^%s/update$' % name, self.ajax_update))
        l.append(url(r'^%s/(\d+)/print$' % name, self.print_one))
        l.append(url(r'^%s/print$' % name, self.print_many))
        #l.append(url(r'^%s/json$' % name, self.json))
        #l.append(url(r'^%s/(\d+)/json$' % name, self.json_one))
        return l

    #~ def view(self,request):
        #~ return self.view_many(request)
    def view_many(self,request):
        #~ msg = "Hello, "+unicode(request.user)
        #~ print msg
        #~ request.user.message_set.create(msg)
        if not self.can_view.passes(request):
            return render.sorry(request)
        r = render.ViewManyReportRenderer(request,True,self)
        #~ if is_editing(request) and self.can_change.passes(request):
            #~ r = render.EditManyReportRenderer(request,True,self)
        #~ else:
            #~ r = render.ViewManyReportRenderer(request,True,self)
        return r.render_to_response()
        
    def renderer(self,request):
        return render.ViewManyReportRenderer(request,False,self)
        
            
    def view_one(self,request,row_num,**kw):
        #print "Report.view_one()", request.path
        if not self.can_view.passes(request):
            return render.sorry(request)
        r = render.ViewOneReportRenderer(row_num,request,True,self,**kw)
        #~ if is_editing(request) and self.can_change.passes(request):
            #~ r = render.EditOneReportRenderer(row_num,request,True,self,**kw)
        #~ else:
            #~ r = render.ViewOneReportRenderer(row_num,request,True,self,**kw)
        return r.render_to_response()

    #~ def view_one_slave(self,request,row_num,slave_name):
        #~ if not self.can_view.passes(request):
            #~ return render.sorry(request)
        #~ r = render.ViewOneReportRenderer(row_num,request,True,self)
        #~ sl = r.get_slave(slave_name)
        #~ slr = render.ViewManyReportRenderer(request,True,sl)
        #~ return slr.render_to_response()

    def pdf_one(self,request,row):
        if not self.can_view.passes(request):
            return render.sorry(request)
        return render.PdfOneReportRenderer(row,request,True,self).render()
        
    def pdf_many(self, request):
        if not self.can_view.passes(request):
            return render.sorry(request)
        return render.PdfManyReportRenderer(request,True,self).render()

        
    def old_json(self, request):
        #print "json:", self
        if not self.can_view.passes(request):
            return None
        qs = self.get_queryset()
        sort = request.GET.get('sort',None)
        if sort:
            sort_dir = request.GET.get('dir','ASC')
            if sort_dir == 'DESC':
                sort = '-'+sort
            qs = qs.order_by(sort)
        offset = request.GET.get('start',None)
        if offset:
            lqs = qs[int(offset):]
        else:
            lqs = qs
        limit = request.GET.get('limit',self.page_length)
        if limit:
            lqs = lqs[:int(limit)]
        rows = [ self.obj2json(row) for row in lqs ]
        d = dict(count=qs.count(),rows=rows)
        s = simplejson.dumps(d,default=unicode)
        #print s
        return HttpResponse(s, mimetype='text/html')
        
        
    #~ def json_one(self,request,row):
        #~ if not self.can_view.passes(request):
            #~ return None
        #~ qs = self.get_queryset()
        #~ rows = [ self.obj2json(qs[int(row)]) ]
        #~ d = dict(count=qs.count(),rows=rows)
        #~ s = simplejson.dumps(d,default=unicode)
        #~ #print s
        #~ return HttpResponse(s, mimetype='text/html')
        
        
    def ajax_update(self,request):
        print request.POST
        return HttpResponse("1", mimetype='text/x-json')

    #~ def flexigrid(self, request):
        #~ if not self.can_view.passes(request):
            #~ return render.sorry(request)
        #~ r = render.FlexigridRenderer(request,True,self)
        #~ return r.render_to_response()
        
    def print_many(self, request):
        if not self.can_view.passes(request):
            return render.sorry(request)
        return render.PdfManyReportRenderer(request,True,self).render(as_pdf=False)

    def print_one(self,request,row):
        if not self.can_view.passes(request):
            return render.sorry(request)
        return render.PdfOneReportRenderer(row,request,True,self).render(as_pdf=False)

    def as_text(self, *args,**kw):
        from lino.django.utils.renderers_text import TextReportRenderer
        return TextReportRenderer(self,*args,**kw).render()
        
    #~ def as_html(self, **kw):
        #~ return render.HtmlReportRenderer(self,**kw).render_to_string()
        
    def get_row_actions(self,renderer):
        l = []
        #l.append( ('dummy',self.dummy) )
        if self.can_change.passes(renderer.request):
            l.append( ('delete',self.delete_selected) )
        return l
            
    def delete_selected(self,renderer):
        for row in renderer.selected_rows():
            print "DELETE:", row.instance
            row.instance.delete()
        renderer.must_refresh()
        
        
#~ class SubReport(Report):
  
    #~ def __init__(self,master,fk_name=None):
    #~ fk = _get_foreign_key(master,self.model,fk_name)
  
    #~ def set_master(self,master):
        #~ self.master = master
        
    #~ def get_queryset(self):
        #~ return document.docitem_set.order_by("pos")
        