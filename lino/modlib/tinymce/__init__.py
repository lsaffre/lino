# -*- coding: UTF-8 -*-
# Copyright 2015 Luc Saffre
# License: BSD (see file COPYING for details)

"""Adds usage of the TinyMCE editor instead of Ext.form.HtmlEditor for
RichTextFields.  See also :attr:`tinymce_root`.  See
`/blog/2011/0523`.  (formerly `use_tinymce`).

"""

from lino.api import ad

TINYMCE3 = True
"""Set this to False if you want Lino to use TinyMCE 4.1.10 instead of
the currently used 3.4.8.  When you do this, windows containing a
TextField don't open, and the JS console says "TypeError: sp is
undefined". That's because we did not yet get Andrew Mayorov's
Ext.ux.TinyMCE to work with TinyMCE 4.

"""


def javascript(url):
    return '<script type="text/javascript" src="{0}"></script>'.format(url)


class Plugin(ad.Plugin):
    "See :doc:`/dev/plugins`."

    needs_plugins = ['lino.modlib.office']  # because of TextFieldTemplate

    site_js_snippets = ['tinymce/tinymce.js']

    url_prefix = 'tinymce'

    # window_width = 600
    # window_height = 500

    document_domain = None
    """When serving static files from a different domain, TinyMCE needs to
    know about this. Typical usage is to specify this in your
    :file:`djangosite_local.py` file (:ref:`lino.djangosite_local`)::

        def setup_site(self):
            ...
            from lino.api.ad import configure_plugin
            configure_plugin('tinymce', document_domain="mydomain.com")

    You must also manually change your static `tiny_mce_popup.js` file
    after each `collectstatic`.

    """

    window_width = 500
    """The initial width of the window to use when editing in own
    window.

    """

    window_height = 400
    """The initial height of the window to use when editing in own
    window.

    """

    field_buttons = (
        "bold,italic,underline,|,justifyleft,justifycenter,justifyright,|,"
        "bullist,numlist,|,outdent,indent,|,undo,redo,|,removeformat,template")
    """The toolbar buttons when editing a field inside a detail form."""

    window_buttons1 = (
        "save,cancel,|,bold,italic,underline,|,justifyleft,justifycenter,"
        "justifyright,fontselect,fontsizeselect,formatselect,|,"
        "search,replace")
    """The first row of toolbar buttons when editing in own window."""
    window_buttons2 = (
        "cut,copy,paste,template,|,bullist,numlist,|,outdent,indent,|,"
        "undo,redo,|,link,unlink,anchor,image,|,code,preview,|,forecolor,"
        "backcolor")
    """The second row of toolbar buttons when editing in own window."""

    window_buttons3 = (
        "insertdate,inserttime,|,spellchecker,advhr,,removeformat,|,"
        "sub,sup,|,charmap,emotions,|,tablecontrols")
    """The third row of toolbar buttons when editing in own window."""

    if TINYMCE3:
        media_name = 'tinymce-3.4.8'
        # media_name = 'tinymce-3.5.11'
    else:
        media_name = 'tinymce-4.1.10'
    """Lino currently includes three versions of TinyMCE, but for
    production sites we still use the eldest version 3.4.8.

    """

    media_root = None
    # media_base_url = "http://www.tinymce.com/js/tinymce/jscripts/tiny_mce/"
    # media_base_url = "http:////tinymce.cachefly.net/4.1/tinymce.min.js"

    def get_used_libs(self, html=False):
        if html is not None:
            if TINYMCE3:
                # yield ("TinyMCE", '3.4.8', "http://www.tinymce.com/")
                yield ("TinyMCE", '3.5.11', "http://www.tinymce.com/")
            else:
                yield ("TinyMCE", '4.1.10', "http://www.tinymce.com/")
            # yield ("Ext.ux.TinyMCE", '0.8.4', "http://twitter.com/xorets")
            yield ("Ext.ux.TinyMCE", '0.8.4', "http://www.byte-force.com")

    def get_js_includes(self, settings, language):
        if TINYMCE3:
            yield self.build_lib_url('tiny_mce.js')
        else:
            yield self.build_lib_url('tinymce.min.js')
        yield settings.SITE.build_static_url("byteforce", "Ext.ux.TinyMCE.js")

    def get_patterns(self):
        from django.conf.urls import url
        from . import views

        rx = '^'

        urlpatterns = [
            url(rx + r'templates/(?P<app_label>\w+)/'
                + r'(?P<actor>\w+)/(?P<pk>\w+)/(?P<fldname>\w+)$',
                views.Templates.as_view()),
            url(rx + r'templates/(?P<app_label>\w+)/'
                + r'(?P<actor>\w+)/(?P<pk>\w+)/(?P<fldname>\w+)/'
                + r'(?P<tplname>\w+)$',
                views.Templates.as_view())]

        return urlpatterns

    def get_row_edit_lines(self, e, panel):
        from lino.modlib.extjs.elems import TextFieldElement
        if isinstance(e, TextFieldElement):
            if e.format == 'html':
                yield "%s.refresh();" % e.as_ext()

    def setup_config_menu(self, site, profile, m):
        if site.user_model is not None:
            mg = site.plugins.office
            m = m.add_menu(mg.app_label, mg.verbose_name)
            m.add_action('tinymce.MyTextFieldTemplates')

    def setup_explorer_menu(self, site, profile, m):
        if site.user_model is not None:
            mg = site.plugins.office
            m = m.add_menu(mg.app_label, mg.verbose_name)
            m.add_action('tinymce.TextFieldTemplates')


