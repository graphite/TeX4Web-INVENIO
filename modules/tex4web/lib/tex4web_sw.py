from invenio.tex4web_core import TeX4Web, _format

import re

class TeX4WebSW(TeX4Web):
    re_swref_remove = re.compile(r"[^a-zA-Z0-9\-:.,']+")

    def __init__(self, image_base):
        self.commands = {
            '\\cref': (TeX4WebSW.cmd_swref,
                        u'<a class="t4w-cref" href="%s">%s</a>',
                        u'/ontology/'),
            '\\dref': (TeX4WebSW.cmd_swref,
                        u'<a class="t4w-dref" href="%s">%s</a>',
                        u'/definitions/'),
            '\\fileref': (TeX4WebSW.cmd_swref,
                        u'<a class="t4w-fileref" href="%s">%s</a>',
                        image_base)
        }

        self.commands.update(TeX4Web.commands)

        super(TeX4Web, self).__init__(u'', u'/definitions/', image_base)

    def cmd_swref(self, cmd, tag, base_url):
        args, err = self.parse_args(cmd, opt_args=1, simple_args=1)
        if err:
            return err

        url = base_url + self.re_swref_remove.sub('_', args[1])
        text = args[0] or args[1]

        return _format(tag, url, text)
