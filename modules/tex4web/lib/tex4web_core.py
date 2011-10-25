#!/usr/bin/python

import re

ERROR_MESSAGE = u'<div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">%s</span></div>'

def escape(text):
    return text.replace('&', '&amp;') \
               .replace('<', '&lt;') \
               .replace('>', '&gt;') \
               .replace('"', '&quot;') \
               .replace("'", '&#39;')

def _format(text, *args):
    return text % args

class _TeX4Web(object):

    re_comment = re.compile(r'((^|[^\\])(\\\\)*)%.*$\n?', re.M)
    re_startspaces = re.compile(r'(^|\n)[ \t]+')
    re_par = re.compile(r'(^|[^\\])\r?\n(\r?\n)+')
    re_active = re.compile(r'(\\[A-Za-z]+\s*|\\[^A-Za-z]|\\$|\$\$?|[{}~&])')
    re_commands = re.compile(r'(\\[A-Za-z]+)\s*')
    re_spaces = re.compile(r'\s+')

    re_dash3 = re.compile(r'(^|[^\-])---([^\-]|$)',)
    re_dash2 = re.compile(r'(^|[^\-])--([^\-]|$)',)

    re_opt_arg = re.compile(r'^\s*\[([^\[\]]*)\]')
    re_opt_arg_cmd = re.compile(r'^\s*\[(.*)\]')
    re_n_simple_arg = re.compile(r'^\s*\{([^{}]*)\}')
    re_star = re.compile(r'^\s*\*')

    re_length_f = re.compile(r'^\d+(in|cm|mm|em|ex|pt|pc|px)$')
    re_url_f = re.compile(r'^https?://')
    re_label_f = re.compile(r'^[A-Za-z_][A-Za-z_.\-]*$')

    re_href = re.compile('href="&&&&t4w-(href|cite)-[^&]*(&[^&]+)*&&&&"')
    re_ref = re.compile('&&&&t4w-(ref|autoref|bibitem)-[^&]*(&[^&]+)*&&&&')

    re_int = re.compile(r'^[0-9]+?$')
    re_alnum = re.compile(r'^[a-zA-Z0-9]+$')

    def __init__(self, data='', urls_base=u'http://', images_base=u'http://'):
        self.title = {'thanks':u'', 'author':u'',
                      'affiliation':u'', 'date':u'', 'title':u'' }
        self.cmd = ''
        self.urls_base = urls_base
        self.images_base = images_base
        self.tokenize(data)

    def parse_document(self, data):
        r""" Parse document. """

        data = data.replace(r'\begin{document}', '')
        data = data.replace(r'\end{document}', '')
        self.tokenize(data)
        result = self.parse_group(root=True)
        #assert self.tokens[self.idx][0] == (None, None)

        # Post-process bibliography references
        for k, v in self.bibitems.iteritems():
            result = result.replace('&&&&t4w-cite-' + k + '&&&&',
                                    '#t4w-bibitem-' + v)
            result = result.replace('&&&&t4w-bibitem-' + k + '&&&&', v)

            # backrefs
            cite_ids = self.cite_ids.get(k, None)
            if cite_ids is None:
                backrefs = ''
            elif len(cite_ids) == 1:
                backrefs = '<a class="t4w-bibitem-backref" href="#' + \
                                cite_ids[0] + '">^</a>'
            else:
                backrefs = '<span class="t4w-bibitem-backref">^</span> '
                name = 'a'
                for id in cite_ids:
                    backrefs += '<a class="t4w-bibitem-backref" href="#' + \
                                id + '"><sup>' + name + '</sup></a> '
                    if name[-1] == 'z':
                        name = name[:-1] + 'aa'
                    else:
                        name = name[:-1] + chr(ord(name[-1])+1)

            result = result.replace('&&&&t4w-bibitem-backrefs-' + v + '&&&&',
                                        backrefs)

        # Post-process other references
        for k, v in self.labels.iteritems():
            result = result.replace('&&&&t4w-href-' + k + '&&&&',
                                    '#t4w-' + v[0] + '-' + v[1])
            result = result.replace(
                    '&&&&t4w-ref-' + k + '&&&&', v[1])
            result = result.replace(
                    '&&&&t4w-eqref-' + k + '&&&&', v[1])
            result = result.replace(
                    '&&&&t4w-autoref-' + k + '&&&&', v[0] + ' ' + v[1])

        # Post-process undefined references
        result = self.re_ref.sub(
                self.error_message('undefined reference'), result)
        result = self.re_href.sub('', result)

        return result

    def tokenize(self, data):
        r""" Preprocess and tokenize data.

            Examples:
            >>> t=TeX4Web(u' aa \\bb { cc'); t.tokens
            [(0, u'aa '), (1, u'\\bb'), (1, u'{'), (0, u' cc'), (None, None)]
            >>> t=TeX4Web(u'\\aa \\bb cc'); t.tokens
            [(1, u'\\aa'), (1, u'\\bb'), (0, u'cc'), (None, None)]
        """

        # Reset
        self.idx = 0        # current index in self.tokens

        self.labels = {}    # label: (cmd, number)
        self.bibitems = {}  # bibitem_label: number
        self.cite_ids = {}  # cite_label: [id1, id2, ...]
        self.counters = {}  # counter_name: number

        self.active_groups = [] # stack of environment names, u'' for groups
        self.env_end = False    # set to true to finish current env

        self.section = None     # current section
        self.appendix = False   # set to True by \\appendix command

        self.tabular = None     # [td_number, (td0_cls,td0_attr)*]
        self.ngroup = None      # (ngroup_number, caption)
        self.equation = None    # equation_number

        self.data = data
        self.tokens = self.data

        # Remove comments
        self.tokens = self.re_comment.sub(u'\\1', self.tokens)

        # Remove spaces at the begining of lines
        self.tokens = self.re_startspaces.sub(u'\\1', self.tokens)

        # Insert \par
        self.tokens = self.re_par.sub(u'\\1\\par\n', self.tokens)

        # Collapse spaces
        self.tokens = self.re_spaces.sub(u' ', self.tokens)

        # Fix dashes
        self.tokens = self.re_dash3.sub(u'\\1\u2014\\2', self.tokens)
        self.tokens = self.re_dash2.sub(u'\\1\u2013\\2', self.tokens)

        # Tokenize and normalize spaces
        self.tokens = self.re_active.split(self.tokens)
        self.tokens = [(n%2, self.re_commands.sub(u'\\1', x))
                        for n,x in enumerate(self.tokens)
                        if n%2 or x]

        # Append sentinel
        self.tokens.append((None, None))

    def cmd_accent(self, cmd, code):
        idx = self.idx

        group = self.check_token_sp((1, '{'))
        while self.tokens[self.idx] == (0, ' '):
            self.idx += 1
        if group:
            if self.check_token_sp((1, '}')):
                return u'\u00a0' + code

        if self.tokens[self.idx][0] != 0:
            if self.tokens[self.idx][1] in self.char_commands:
                self.tokens[self.idx] = (0, self.char_commands[self.tokens[self.idx][1]])
            else:
                return self.error_message('Accent can only be applied to normal characters')

        self.tokens[self.idx] = (0, self.tokens[self.idx][1][0] + code + \
                                        self.tokens[self.idx][1][1:])

        self.idx = idx
        return u''

    def cmd_appendix(self, cmd):
        if self.appendix:
            return self.error_message(_format('duplicated %s command', cmd))
        self.appendix = True
        return u''

    def cmd_caption(self, cmd):
        if self.active_groups[-1] not in ('table', 'figure'):
            return self.error_message(_format('command %s can only '
                    'be used in table or figure environments', cmd))

        args, err = self.parse_args(cmd, group_args=1, opt_args=1)
        if err:
            return err

        self.ngroup[1] = args[1]
        return u''

    def cmd_cite(self, cmd, tag, mtag):
        args, err = self.parse_args(cmd, opt_args=1, simple_args=1)

        if err:
            return err

        if args[0]:
            args[0] = ', ' + args[0]

        bibitems = []
        for label in args[1].split(','):
            cite_id = 't4w-cite-' + str(self.increment_counter('cite_id'))
            self.cite_ids.setdefault(label, [])
            self.cite_ids[label].append(cite_id)
            bibitems.append( _format(mtag, cite_id,
                _format('&&&&t4w-cite-%s&&&&', label),
                _format('&&&&t4w-bibitem-%s&&&&', label)))

        return _format(tag, ', '.join(bibitems) + args[0])

    def cmd_color(self, cmd, tag):
        args, err = self.parse_args(cmd, simple_args=1)
        if err:
            return err

        arg = self.parse_group(is_open=True)
        return _format(tag, args[0], arg)

    def cmd_group_otag(self, cmd, tag):
        arg = self.parse_group(is_open=True)
        return _format(tag, arg)

    def cmd_group_tag(self, cmd, tag):
        arg = self.parse_group_arg()
        if not arg:
            arg = self.error_message(_format('missing argument for %s', cmd))
        return _format(tag, arg)

    def cmd_href(self, cmd, tag):
        args, err = self.parse_args(cmd,
                simple_args=1, group_args=(cmd == '\\href' and 1 or 0))
        if err:
            return err
        url = args[0]
        text = args[cmd == '\\href' and 1 or 0]
        if not self.re_url_f.match(url):
            url = self.urls_base + url
            #text = self.error_message('incomplete URL') + text
        return _format(tag, url, text)

    def cmd_includegraphics(self, cmd, tag):
        args, err = self.parse_args(cmd, opt_args=1, simple_args=1, allow_cmd=True)
        if err:
            return err

        size = ''
        params = self.parse_dict(args[0])
        for key, value in params.iteritems():
            if key not in ('width', 'height'):
                return self.error_message(_format('unknown params for %s', cmd))

            if filter(lambda a: a in value, self.length_commands):
                value = ''
            elif not self.re_length_f.match(value or ''):
                return self.error_message(
                        _format('bad value for %s parameter for %s', key, cmd))
            size += _format('%s:%s;', key, value)

        url = args[1]
        if not self.re_url_f.match(url):
            if '.' not in url:
                url +='.png'
            url = self.images_base + url

        return _format(tag, size, url)

    def cmd_maketitle(self, cmd):
        result = ''
        for a in ['title', 'author', 'affiliation', 'date']:
            result +=_format(_div_tag('title'), self.title.get(a,''))
        return result

    def cmd_math(self, cmd, env, tag, numbered=False):
        r""" Parse math group.

            Examples:
            >>> t=TeX4Web(u'x^2$'); t.cmd_math('$', '', u'<%s>'), t.idx
            (u'<x^2>', 2)
            >>> t=TeX4Web(u'x^2$ b'); t.cmd_math('$', '', u'<%s>'), t.idx
            (u'<x^2>', 2)
            >>> t=TeX4Web(u'x^2 b'); t.cmd_math('$', '', u'<%s>'), t.idx
            (u'<div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">formula is not closed</span></div>', 0)
            >>> t=TeX4Web(u'x^2 \par b'); t.cmd_math('$', '', u'<%s>'), t.idx
            (u'<div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">formula is not closed</span></div>', 0)
            >>> t=TeX4Web(u'\\alpha x$'); t.cmd_math('$', '', u'<%s>'), t.idx
            (u'<\\alpha x>', 3)
        """

        if env == 'err':
            return error_message(_format('unexpected %s', cmd))

        result = u''
        err = u'formula is not closed'

        old_idx = self.idx
        while self.tokens[self.idx][0] is not None:
            token = self.tokens[self.idx]
            self.idx += 1

            # TODO: verify grouping and environments
            if token[0] == 1:
                if cmd == '$' and token[1] == '$':
                    err = u''
                    break
                elif cmd == '$$' and token[1] == '$$':
                    err = u''
                    break
                elif cmd == '\(' and token[1] == '\)':
                    err = u''
                    break
                elif cmd == '\[' and token[1] == '\]':
                    err = u''
                    break
                elif cmd == '\\begin' and token[1] == '\\end':
                    _old_idx = self.idx
                    _env = self.parse_simple_arg()
                    if _env == env:
                        err = u''
                        break
                    self.idx = _old_idx
                elif token[1] == '\\par':
                    #err = u'paragraph ended inside a formula'
                    err = u'formula is not closed'
                    break
                elif numbered and token[1] == '\\label':
                    self.cmd_label(token[1])
                    token = (0, u'')
                elif numbered and token[1] == '\\nonumber':
                    self.equation = str(self.decrement_counter('equation'))
                    token = (0, u'')
                elif numbered and token[1] == '\\\\':
                    self.equation = str(self.increment_counter('equation'))
                elif self.re_commands.match(token[1]):
                    token = (1, token[1] + u' ')

            result += token[1]

        if err:
            self.idx = old_idx
            return self.error_message(err)

        # A hack to restore -- and --- in math mode
        result = result.replace(u'\u2013', u'--').replace(u'\u2014', u'---')

        return _format(tag, result)

    def cmd_newline(self, cmd, tag, tag_a, stab_t, etab_t):
        if cmd == '\\\\':
            if self.active_groups[-1] == 'tabular':
                cls = ('def', '')
                self.tabular[0] = 1
                if len(self.tabular) > 1:
                    cls = self.tabular[1]
                return self.commands['&amp;'][2] + etab_t + \
                       stab_t + _format(self.commands['&amp;'][1], *cls)
            arg = self.parse_opt_arg()
            if arg:
                # We've got a height arg
                if self.re_length_f.match(arg):
                    return _format(tag_a, arg)
                else: # wrong arg format
                    return tag + self.error_message(
                            _format('wrong argument for %s', cmd))
        return tag

    def cmd_newtab(self, cmd, stab, etab):
        if self.active_groups[-1] != 'tabular':
            return self.error_message(_format('character %s can only '
                'be used inside tabular environment', cmd))
        cls = ('def', '')
        n = self.tabular[0]+1
        self.tabular[0] = n
        if len(self.tabular) > n:
            cls = self.tabular[n]
        return etab + _format(stab, *cls)

    def cmd_package(self, cmd):
        args, err = self.parse_args(cmd, group_args=1)
        if err:
            return err
        return u''

    def cmd_replace(self, cmd, repl):
        return repl

    def cmd_rule(self, cmd, tag):
        args, err = self.parse_args(cmd, simple_args=2, opt_args=1)
        if err:
            return err
        return _format(tag, args[1], args[2])

    def cmd_vspace(self, cmd, tag):
        args, err = self.parse_args(cmd, simple_args=1)
        if err:
            return err
        return _format(tag, args[0])

    def cmd_section(self, cmd, tag, ntag, stag):
        if self.active_groups != [u'']:
            return self.error_message(_format('command %s can be used only in top-level group', cmd))
        if cmd == '\\section':
            level = 0
        elif cmd == '\\subsection':
            level = 1
        else:
            level = 2

        star = False
        if self.tokens[self.idx][0] == 0:
            m_star = self.re_star.match(self.tokens[self.idx][1])
            if m_star and not self.tokens[self.idx][1][m_star.end():].strip():
                self.idx += 1
                star = True

        if not star:
            if self.appendix:
                numbers = self.increment_sub_counters('appendix', level)
                if numbers[0] == 0:
                    numbers[0] = ''
                elif numbers[0]-1 <= ord('Z')-ord('A'):
                    numbers[0] = chr(ord('A') + numbers[0] - 1)
                else:
                    numbers[0] = 'A' + str(numbers[0])
                self.section = (cmd[1:], '.'.join([str(x) for x in numbers]))
            else:
                numbers = self.increment_sub_counters('section', level)
                self.section = (cmd[1:], '.'.join([str(x) for x in numbers]))

        result = self.parse_group_arg()
        if not result:
            result = self.error_message(_format('missing argument for %s', cmd))

        # Ignore next \par
        self.check_token_sp((1, '\\par'))

        if not star:
            result = _format(ntag, self.section[1]) + result
            return _format(tag, self.section[1], result)
        else:
            return _format(stag, result)

    def cmd_textcolor(self, cmd, tag):
        args, err = self.parse_args(cmd, simple_args=1)
        if err:
            return err

        arg = self.parse_group_arg()
        if not arg:
            arg = self.error_message(_format('missing argument for %s', cmd))

        return _format(tag, args[0], arg)

    def cmd_title(self, cmd):
        arg = self.parse_group_arg()
        if not arg:
            arg = self.error_message(_format('missing argument for %s', cmd))
        else:
            self.title[cmd[1:]]=arg
        return ''

    def cmd_env(self, cmd):
        env = self.parse_simple_arg()
        if not env:
            return self.error_message(_format('missing argument for %s', cmd))

        if env in self.environments:
            e = self.environments[env]

            if cmd == '\\begin':
                return e[0](self, '\\begin', env, *e[1:])
            else:
                if self.active_groups[-1] != env:
                    return self.error_message(_format(
                            'unexpected \\end{%s}', env))
                self.env_end = True
                return u''

        return self.error_message(_format('unknown environment %s', env))

    def env_group(self, cmd, env, tag):
        content = self.parse_group(is_env=env)
        return _format(tag, content)

    def env_group_section(self, cmd, env, tag):
        """ Parse section-like environment. """

        if self.active_groups != [u'']:
            return self.error_message(_format('environment %s can be used only in top-level group', env))

        result = self.env_group(cmd, env, tag)

        # Ignore next \par
        self.check_token_sp((1, '\\par'))

        return result

    def cmd_item(self, cmd, stag, etag, dtag=u''):
        if self.active_groups[-1] not in (
                'itemize', 'enumerate', 'description'):
            return self.error_message(_format('unexpected %s', cmd))

        result = etag + stag

        if self.active_groups[-1] == 'description':
            arg = self.parse_opt_arg()
            result += _format(dtag, arg)

        return result

    def env_list(self, cmd, env, tag):
        err = u''
        if not self.check_token_sp((1, '\\item')):
            err = self.error_message('missing \\item')

        self.active_groups.append(env)
        result = self.cmd_item('\\item',
                self.commands['\\item'][1], u'', self.commands['\\item'][3])
        self.active_groups.pop()

        result += err
        result += self.parse_group(is_env=env)
        result += self.commands['\\item'][2]
        result = _format(tag, result)

        # Ignore next \par
        self.check_token_sp((1, '\\par'))

        return result

    def cmd_bibitem(self, cmd, stag, etag):
        if self.active_groups[-1] != 'thebibliography':
            return self.error_message(_format('unexpected %s', cmd))

        args, err = self.parse_args(cmd, opt_args=1, simple_args=1)
        counter = str(self.increment_counter('bibitem'))
        number = counter
        if not err:
            if not args[1]:
                err = self.error_message('label is empty')
            elif args[1] in self.bibitems:
                err = self.error_message('duplicated bibitem label')
            else:
                if args[0]:
                    number = args[0]
                self.bibitems[args[1]] = number
                err = u''

        return etag + _format(stag, number, counter,
                    _format('&&&&t4w-bibitem-backrefs-%s&&&&', number)) + err

    def env_thebibliography(self, cmd, env, tag):
        if self.active_groups != [u'']:
            return self.error_message(_format('environment %s can be used only in top-level group', env))

        err = u''
        arg = self.parse_simple_arg()
        if not arg:
            err = self.error_message(_format(
                    'missing argument for %s{%s}', cmd, env))

        # Ignore next \par
        self.check_token_sp((1, '\\par'))

        # Add thanks to references
        result = self.title['thanks']
        if not self.check_token_sp((1, '\\bibitem')):
            stag1 = self.commands['\\bibitem'][1]

            number = str(self.increment_counter('bibitem'))
            result += _format(stag1, number, number, number)
            result += self.error_message('missing \\bibitem')
        else:
            self.active_groups.append(env)
            result += self.cmd_bibitem('\\bibitem',
                        self.commands['\\bibitem'][1], u'')
            self.active_groups.pop()

        result += self.parse_group(is_env=env)
        result += self.commands['\\bibitem'][2]
        result = _format(tag, err, result)

        # Ignore next \par
        self.check_token_sp((1, '\\par'))

        return result

    def env_math(self, cmd, env, tag):
        result = self.cmd_math(cmd, env, tag)
        if env == 'displaymath':
            # Ignore next \par
            self.check_token_sp((1, '\\par'))
        return result

    def env_nmath(self, cmd, env, tag, mtag, ntag):
        self.equation = str(self.increment_counter('equation'))
        old_equation_number = int(self.equation)
        self.active_groups.append(env)
        result = self.cmd_math(cmd, env, mtag, numbered=True)
        self.active_groups.pop()

        numbers = ''
        for i in range(int(self.equation)-old_equation_number+1):
            numbers+=_format(ntag, old_equation_number+i, old_equation_number+i)
        result = _format(tag, result, numbers)
        self.equation = None

        # Ignore next \par
        self.check_token_sp((1, '\\par'))

        return result

    def env_tabular(self, cmd, env, tag):
        if self.tabular is not None:
            return self.error_message(
                    'nested tabular environments are not supported')

        self.tabular = [1,]

        err = u''
        arg = self.parse_simple_arg(nested=True)
        if not arg:
            err = self.error_message(_format(
                'missing argument for %s{%s}', cmd, env))
        else:
            idx = 0
            while idx < len(arg):
                c = arg[idx]
                idx += 1
                if c in 'lcr':
                    self.tabular.append((c, ''))
                elif c in 'pmb':
                    m = self.re_n_simple_arg.match(arg[idx:])
                    if not m:
                        err += self.error_message(_format(
                            'missing argument for table spec char %s', c))
                        break
                    if not self.re_length_f.match(m.group(1)):
                        err += self.error_message(_format(
                            'wrong argument for table spec char %s', c))
                        idx += m.end()
                        break
                    self.tabular.append(
                            (c, _format('style="width: %s"', m.group(1))))
                    idx += m.end()

                else:
                    err += self.error_message(_format(
                            'table spec char %s is not supported', c))
                    break

        if err:
            self.tabular = [1,]

        cls = ('def', '')
        if len(self.tabular) > 1:
            cls = self.tabular[1]

        tbody = self.commands['\\\\'][3] + \
                _format(self.commands['&amp;'][1], *cls) + \
                self.parse_group(is_env=env) + \
                self.commands['&amp;'][2] + \
                self.commands['\\\\'][4]

        self.tabular = None
        return err + _format(tag, tbody)

    def cmd_label(self, cmd):
        if self.active_groups != [u'']:
            for x in self.active_groups:
                if x in ('figure', 'table', 'equation', 'eqnarray', 'align'):
                    break
            else:
                return self.error_message(_format('command %s can be used only in '
                    'top-level group or in table or figure environments', cmd))

        if self.active_groups==[u''] and self.section is None:
            return self.error_message(_format('command %s can be '
                    'used only after section command', cmd))

        args, err = self.parse_args(cmd, simple_args=1)
        if err:
            return err

        if not args[0]:
            return self.error_message('label is empty')

        if args[0] in self.labels:
            return self.error_message('duplicated label')

        if self.equation:
            self.labels[args[0]] = ('equation', self.equation)
        elif self.ngroup:
            self.labels[args[0]] = (self.active_groups[-1], self.ngroup[0])
        else:
            self.labels[args[0]] = self.section

        return u''

    def cmd_ref(self, cmd, tag):
        args, err = self.parse_args(cmd, simple_args=1)
        if err:
            return err

        return _format(tag,
                _format('&&&&t4w-href-%s&&&&', args[0]),
                _format('&&&&t4w-%s-%s&&&&', cmd[1:], args[0]))

    def env_ngroup(self, cmd, env, tag):
        if self.active_groups != [u'']:
            return self.error_message(_format('environment %s can be used only in top-level group', env))
        self.ngroup = [str(self.increment_counter(env)),
                        self.error_message(_format('missing %s caption', env))]
        # ignore optional argument
        self.parse_args(cmd, opt_args=1)
        content = self.parse_group(is_env=env)
        result = _format(tag, content, self.ngroup[0], self.ngroup[1])
        self.ngroup = None
        return result

    def cmd_todo(self, cmd, *args):
        return self.error_message(_format('command %s is not implemented yet', cmd))

    def env_todo(self, cmd, env, *args):
        return self.error_message(_format('envitonment %s is not implemented yet', env))

    def increment_counter(self, counter):
        r""" Increment counter by one and return new value.

            Example:
            >>> t4w = TeX4Web()
            >>> t4w.increment_counter('x')
            1
            >>> t4w.increment_counter('x')
            2
        """
        number = self.counters.get(counter, 0) + 1
        self.counters[counter] = number
        return number

    def decrement_counter(self, counter):
        r""" Decrement counter by one and return new value.

            Example:
            >>> t4w = TeX4Web()
            >>> t4w.increment_counter('x')
            1
            >>> t4w.decrement_counter('x')
            0
        """
        number = self.counters.get(counter, 0) - 1
        self.counters[counter] = number
        return number

    def increment_sub_counters(self, counter, level):
        r""" Increment multilevel counter and return new index.

            Example:
            >>> t4w = TeX4Web()
            >>> t4w.increment_sub_counters('x', 1)
            [0, 1]
            >>> t4w.increment_sub_counters('x', 2)
            [0, 1, 1]
            >>> t4w.increment_sub_counters('x', 1)
            [0, 2]
            >>> t4w.increment_sub_counters('x', 0)
            [1]
            >>> t4w.increment_sub_counters('x', 2)
            [1, 0, 1]
        """
        x = 0
        result = []
        while True:
            if x <= level:
                if x == level:
                    self.counters.setdefault(counter + str(x), 0)
                    self.counters[counter + str(x)] += 1
                result.append(self.counters.setdefault(counter + str(x), 0))
            elif counter + str(x) in self.counters:
                self.counters[counter + str(x)] = 0
            else:
                return result
            x += 1

    def error_message(self, message):
        r""" Format error message.

            Example:
            >>> TeX4Web().error_message('xxx')
            u'<div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">xxx</span></div>'
        """
        return _format(ERROR_MESSAGE, message)

    def check_token_sp(self, token):
        r""" Check that token is next or next after space and skip it. """
        if self.tokens[self.idx] == token:
            self.idx += 1
            return True
        elif self.tokens[self.idx] == (0, ' ') and \
                 self.tokens[self.idx+1] == token:
            self.idx += 2
            return True
        else:
            return False

    def parse_args(self, cmd, opt_args=0, simple_args=0, group_args=0, allow_cmd=False):

        result = ([], None)
        old_idx = self.idx

        for x in range(opt_args):
            result[0].append(self.parse_opt_arg(allow_cmd=allow_cmd))

        for x in range(simple_args):
            arg = self.parse_simple_arg()
            if arg is None:
                self.idx = old_idx
                return [], self.error_message(_format('missing argument for %s', cmd))
            result[0].append(arg)

        for x in range(group_args):
            arg = self.parse_group_arg()
            if arg is None:
                self.idx = old_idx
                return [], self.error_message(_format('missing argument for %s', cmd))
            result[0].append(arg)

        return result

    def parse_group(self, root=False, is_open=False, is_env=False):
        r""" Parse LaTeX group.

            Arguments:
              root:     True for root group of the document
              is_open:  True for open group (like text after \bf)

            Examples of root groups (the whole document):
            >>> t=TeX4Web(u' abc{d{e}f}ghk '); t.parse_group(root=True), t.tokens[t.idx][1]
            (u'abcdefghk ', None)
            >>> t=TeX4Web(u' {  abc{d{e}f}ghk } '); t.parse_group(root=True), t.tokens[t.idx][1]
            (u' abcdefghk  ', None)
            >>> t=TeX4Web(u' abc{d{e}f}gh}k '); t.parse_group(root=True), t.tokens[t.idx][1]
            (u'abcdefgh<div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">extra } character</span></div>k ', None)

            Examples of open groups:
            >>> t=TeX4Web(u' {abc{d{e}f}} gh } k '); t.parse_group(is_open=True), t.tokens[t.idx][1]
            (u'abcdef gh ', u'}')
            >>> t=TeX4Web(u' {abc{d{e}f}} gh  k '); t.parse_group(is_open=True), t.tokens[t.idx][1]
            (u'abcdef gh k ', None)

            Examples of non-root groups:
            >>> t=TeX4Web(u' {  abc{d{e}f}gh } k '); t.parse_group(), t.tokens[t.idx][1]
            (u' abcdefgh ', u' k ')
            >>> t=TeX4Web(u' {  abc{d{e}f}ghk '); t.parse_group(), t.tokens[t.idx][1]
            (u' abcdefghk <div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">group was not closed</span></div>', None)

            Examples of wrong groups:
            >>> t=TeX4Web(u' abc'); t.parse_group(), t.tokens[t.idx][1]
            (u'<div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">begin group character { not found</span></div>', u'abc')
            """

        result = u''

        if not root and not is_open and not is_env:
            if not self.check_token_sp((1, '{')):
                return self.error_message('begin group character { not found')

        if not is_open:
            self.active_groups.append(is_env or u'')

        # Find next token
        while self.tokens[self.idx][0] is not None:
            token = self.tokens[self.idx]
            self.idx += 1
            command = escape(token[1])

            if token[0] == 0:
                # Not a command
                result += command
                continue

            if command == '{':
                self.idx -= 1
                result += self.parse_group()

            elif command == '}':
                if root or is_env:
                    result += self.error_message('extra } character')
                elif is_open:
                    self.idx -= 1
                    return result
                else:
                    self.active_groups.pop()
                    return result

            elif is_open and command == '\\end':
                self.idx -= 1
                return result

            elif command in self.commands:
                c = self.commands[command]
                self.cmd = command[1:]
                result += c[0](self, command, *c[1:])
                if self.env_end: # XXX: better design ?
                    self.env_end = False
                    self.active_groups.pop()
                    return result
            elif command in self.char_commands:
                result += self.char_commands[command]
            else:
                result += self.error_message(_format(
                    'unknown command %s', command))

        # End of document was reached

        # Add error message if needed
        if not root and not is_open:
            if is_env:
                result += self.error_message(_format(
                    'environment %s was not closed', is_env))
            else:
                result += self.error_message('group was not closed')
        elif is_env:
            result += self.error_message(_format(
                'environment %s was not closed', self.environments[-1]))

        if not is_open:
            self.active_groups.pop()
        return result

    def parse_group_arg(self):
        r""" Parse group argument in {}.

            Examples:
            >>> t=TeX4Web(u' { xx {yy} zz }'); t.parse_group_arg(), t.tokens[t.idx][1]
            (u' xx yy zz ', None)
            >>> t=TeX4Web(u' { xx {yy} zz '); t.parse_group_arg(), t.tokens[t.idx][1]
            (u' xx yy zz <div class="t4w-error"><img title="Show error" src="/tex4web/error.png" class="t4w-error"/><span class="t4w-error">group was not closed</span></div>', None)
            >>> t=TeX4Web(u' xx {yy} zz '); t.parse_group_arg(), t.tokens[t.idx][1]
            (None, u'xx ')
        """
        if self.tokens[self.idx] == (1, '{') or \
                (self.tokens[self.idx] == (0, ' ') and \
                 self.tokens[self.idx+1] == (1, '{')):
            return self.parse_group()
        else:
            return None

    def parse_dict(self, str):
        r""" Parses a string like "key1=val1,key2=val2,key3" into a dict """

        result = {}
        for s in str.split(','):
            p = s.split('=', 1)
            if len(p) == 2:
                result[p[0]] = p[1]
            else:
                pass

        return result

    def parse_opt_arg(self, allow_cmd=False):
        r""" Parse optional argument in [].

            Warning: this function modifies self.tokens in order to split opt_arg

            Examples:
            >>> t=TeX4Web(u' [  xxx ] yyy'); t.parse_opt_arg(), t.tokens, t.idx
            (u'xxx', [(0, u'[ xxx ]'), (0, u' yyy'), (None, None)], 1)
            >>> t=TeX4Web(u' [  xxx  yyy'); t.parse_opt_arg(), t.tokens, t.idx
            (u'', [(0, u'[ xxx yyy'), (None, None)], 0)
        """
        token = self.tokens[self.idx]
        if token[0] != 0:
            return u''

        if allow_cmd:
            result = self.parse_cmd_arg()
            if result:
                return result

        m_opt_arg = self.re_opt_arg.match(token[1])
        if m_opt_arg:
            # Vova: what is this case??
            if m_opt_arg.end() < len(token[1]):
                # Split current token
                self.tokens.insert(self.idx, (0, token[1][:m_opt_arg.end()]))
                self.tokens[self.idx+1] = (0, token[1][m_opt_arg.end():])
            self.idx += 1
            return escape(m_opt_arg.group(1).strip())

        return u''

    def parse_simple_arg(self, nested=False, unescape=True):
        r""" Parse simple argument in {}.

            Examples:
            >>> t=TeX4Web(u' {  xxx } yyy'); t.parse_simple_arg(), t.tokens[t.idx][1]
            (u'xxx', u' yyy')
            >>> t=TeX4Web(u' {  xxx  yyy'); t.parse_simple_arg(), t.tokens[t.idx][1]
            (None, u'{')
            >>> t=TeX4Web(u' {  xxx{ z} }'); t.parse_simple_arg(), t.tokens[t.idx][1]
            (None, u'{')
            >>> t=TeX4Web(u' {  xxx{ z} }'); t.parse_simple_arg(1), t.tokens[t.idx][1]
            (u'xxx{ z}', None)
            >>> t=TeX4Web(u' {  xxx\n\n }'); t.parse_simple_arg(), t.tokens[t.idx][1]
            (None, u'{')
        """
        old_idx = self.idx

        if not self.check_token_sp((1, '{')):
            return None

        result = u''
        level = 1
        while self.tokens[self.idx][0] is not None:
            token = self.tokens[self.idx]
            self.idx += 1
            if token[0] == 0:
                result += escape(token[1])
            elif nested and token[1] == '{':
                level += 1
                result += '{'
            elif token[1] == '}':
                level -= 1
                if level == 0:
                    return result.strip()
                result += '}'
            elif unescape and token[1] in self.char_commands:
                result += self.char_commands[token[1]][1]
            else:
                self.idx = old_idx
                return None

        self.idx = old_idx
        return None

    def parse_cmd_arg(self):
        end_idx = self.idx
        for i,t in enumerate(self.tokens[self.idx:self.idx+5]):
            if ']' in t:
                end_idx+=i
                break
        if end_idx==self.idx:
            return None
        cmd_arg = ''.join([a[1] for a in self.tokens[self.idx:end_idx+1]])
        self.idx = end_idx+1
        return cmd_arg[1:-1]

def _span_tag(cls=''):
    return u'<span class="t4w-' + cls + '">%s</span>'

def _div_tag(cls=''):
    return u'<div class="t4w-' + cls + '">%s</div>'

class TeX4Web(_TeX4Web):
    char_commands = {
            '\\#': u'#', '\\$': u'$', '\\%': u'%',
            '\\&amp;': u'&amp;', '\\_':u'_', '\\{': u'{',
            '\\}': u'}', '\\i': u'\u0131'
    }

    length_commands = ['\\linewidth', '\\textwidth']

    commands = {
        # Out name
        '\\TeXForWeb': (_TeX4Web.cmd_replace,
                        u'<span class="t4w-math math">'\
                        u'<script type="math/tex">\TeX^4Web</script>'\
                        u'</span>'),
        '\\usepackage':(_TeX4Web.cmd_package,),
        '\\protect':(_TeX4Web.cmd_replace, u''),

        # Spacing
        '\\ ':      (_TeX4Web.cmd_replace, u' '),
        '\\-':      (_TeX4Web.cmd_replace, u''),
        '\\bigskip':(_TeX4Web.cmd_replace, u'<br/>'),
        '\\medskip':(_TeX4Web.cmd_replace, u'<br/>'),
        '\\smallskip':(_TeX4Web.cmd_replace, u'<br/>'),
        '\\quad':   (_TeX4Web.cmd_replace, u'\u2001'),
        '\\qquad':  (_TeX4Web.cmd_replace, u'\u2001\u2001'),
        '\\enspace':(_TeX4Web.cmd_replace, u'\u2002'),
        '\\;':      (_TeX4Web.cmd_replace, u'\u2004'),
        '\\:':      (_TeX4Web.cmd_replace, u'\u2005'),
        '\\,':      (_TeX4Web.cmd_replace, u'\u2006'),
        '\\thinspace':  (_TeX4Web.cmd_replace, u'\u200A'),

        # Special chars from CK Editor
        '\\dots': (_TeX4Web.cmd_replace, '&hellip;'),
        '\\texteuro': (_TeX4Web.cmd_replace, '&euro;'),
        '\\textquoteleft': (_TeX4Web.cmd_replace, '&lsquo;'),
        '\\textquoteright': (_TeX4Web.cmd_replace, '&rsquo;'),
        '\\textquotedblleft': (_TeX4Web.cmd_replace, '&ldquo;'),
        '\\textquotedblright': (_TeX4Web.cmd_replace, '&rdquo;'),
        '!`': (_TeX4Web.cmd_replace, '&iexcl;'),
        '\\textcent': (_TeX4Web.cmd_replace, '&cent;'),
        '\\pounds': (_TeX4Web.cmd_replace, '&pound;'),
        '\\textcurrency': (_TeX4Web.cmd_replace, '&curren;'),
        '\\textyen': (_TeX4Web.cmd_replace, '&yen;'),
        '\\splitvert': (_TeX4Web.cmd_replace, '&brvbar;'),
        '\\S': (_TeX4Web.cmd_replace, '&sect;'),
        '\\copyright': (_TeX4Web.cmd_replace, '&copy;'),
        '\\textordfeminine': (_TeX4Web.cmd_replace, '&ordf;'),
        '\\textregistered': (_TeX4Web.cmd_replace, '&reg;'),
        '\\cdot': (_TeX4Web.cmd_replace, '&middot;'),
        '\\textordmasculine': (_TeX4Web.cmd_replace, '&ordm;'),
        '?`': (_TeX4Web.cmd_replace, '&iquest;'),
        '\\DH': (_TeX4Web.cmd_replace, '&ETH;'),
        '\\Thorn': (_TeX4Web.cmd_replace, '&THORN;'),
        '\\dh': (_TeX4Web.cmd_replace, '&eth;'),
        '\\thorn': (_TeX4Web.cmd_replace, '&thorn;'),
        '\\textquotestraightbase': (_TeX4Web.cmd_replace, '&sbquo;'),
        '\\textquotestraightdblbase': (_TeX4Web.cmd_replace, '&bdquo;'),
        '\\texttrademark': (_TeX4Web.cmd_replace, '&trade;'),
        '\\blackdiamond': (_TeX4Web.cmd_replace, '&diams;'),
        '\\prime': (_TeX4Web.cmd_replace, '&prime;'),
        '\\second': (_TeX4Web.cmd_replace, '&Prime;'),
        '\\diagup': (_TeX4Web.cmd_replace, '&frasl;'),
        '\\leftarrow': (_TeX4Web.cmd_replace, '&larr;'),
        '\\uparrow': (_TeX4Web.cmd_replace, '&uarr;'),
        '\\rightarrow': (_TeX4Web.cmd_replace, '&rarr;'),
        '\\downarrow': (_TeX4Web.cmd_replace, '&darr;'),
        '\\leftrightarrow': (_TeX4Web.cmd_replace, '&harr;'),
        '\\dlsh': (_TeX4Web.cmd_replace, '&crarr;'),
        '\\Leftarrow': (_TeX4Web.cmd_replace, '&lArr;'),
        '\\Uparrow': (_TeX4Web.cmd_replace, '&uArr;'),
        '\\Rightarrow': (_TeX4Web.cmd_replace, '&rArr;'),
        '\\Downarrow': (_TeX4Web.cmd_replace, '&dArr;'),
        '\\Leftrightarrow': (_TeX4Web.cmd_replace, '&hArr;'),
        '\\textasteriskcentered': (_TeX4Web.cmd_replace, '&lowast;'),

        '~':        (_TeX4Web.cmd_replace, u'&nbsp;'),

        # Ligatures
        '\\ae':     (_TeX4Web.cmd_replace, u'\u00e6'),
        '\\AE':     (_TeX4Web.cmd_replace, u'\u00c6'),
        '\\oe':     (_TeX4Web.cmd_replace, u'\u0153'),
        '\\OE':     (_TeX4Web.cmd_replace, u'\u0152'),
        '\\aa':     (_TeX4Web.cmd_replace, u'\u00e5'),
        '\\AA':     (_TeX4Web.cmd_replace, u'\u00c5'),
        '\\o':      (_TeX4Web.cmd_replace, u'\u00f8'),
        '\\O':      (_TeX4Web.cmd_replace, u'\u00d8'),
        '\\ss':     (_TeX4Web.cmd_replace, u'\u00df'),

        # Accents
        '\\`':      (_TeX4Web.cmd_accent, u'\u0300'),
        '\\&#39;':  (_TeX4Web.cmd_accent, u'\u0301'),
        '\\^':      (_TeX4Web.cmd_accent, u'\u0302'),
        '\\&quot;': (_TeX4Web.cmd_accent, u'\u0308'),
        '\\H':      (_TeX4Web.cmd_accent, u'\u030B'),
        '\\~':      (_TeX4Web.cmd_accent, u'\u0303'),
        '\\c':      (_TeX4Web.cmd_accent, u'\u0327'),
        '\\=':      (_TeX4Web.cmd_accent, u'\u0304'),
        '\\b':      (_TeX4Web.cmd_accent, u'\u0332'),
        '\\.':      (_TeX4Web.cmd_accent, u'\u0307'),
        '\\d':      (_TeX4Web.cmd_accent, u'\u0323'),
        '\\r':      (_TeX4Web.cmd_accent, u'\u030a'),
        '\\u':      (_TeX4Web.cmd_accent, u'\u0306'),
        '\\v':      (_TeX4Web.cmd_accent, u'\u030c'),
        '\\t':      (_TeX4Web.cmd_accent, u'\u0361'),

        # Newlines
        '\\/':      (_TeX4Web.cmd_replace, u''),
        '\\par':    (_TeX4Web.cmd_replace, u'<br class="t4w-par" />\n\n'),
        '\\newline':(_TeX4Web.cmd_newline,
                        u'<br class="t4w-newline" />\n'),
        '\\\\':     (_TeX4Web.cmd_newline,
                        u'<br class="t4w-newline" />\n',
                        u'<br class="t4w-newline" style="padding-bottom: %s" />\n',
                        u'<tr>', u'</tr>\n'),

        '&amp;':    (_TeX4Web.cmd_newtab,
                        u'<td class="t4w-tabular-%s" %s>', u'</td>'),

        # Formatting
        '\\noindent':   (_TeX4Web.cmd_replace, u''),
        '\\centerline': (_TeX4Web.cmd_group_tag, _div_tag('center')),
        '\\mbox':       (_TeX4Web.cmd_group_tag, _span_tag('mbox')),
        '\\rule':       (_TeX4Web.cmd_rule, u'<hr style="width:%s; height:%s; background-color: black;"/>'),
        '\\vspace':     (_TeX4Web.cmd_vspace, u'<div style="height:%s"></div>'),
        '\\footnote':   (_TeX4Web.cmd_group_tag, '<span class="t4w-it">(%s)</span>'), # TODO: update later

        # Math
        '$':        (_TeX4Web.cmd_math, '',
                        u'<span class="t4w-math math">'
                        u'<script type="math/tex">%s</script>'
                        u'</span>'),
        '\\(':      (_TeX4Web.cmd_math, '',
                        u'<span class="t4w-math math">'
                        u'<script type="math/tex">%s</script>'
                        u'</span>'),
        '\\)':      (_TeX4Web.cmd_math, 'err', u''), # XXX
        '$$':       (_TeX4Web.cmd_math, '',
                        u'\n<div class="t4w-displaymath math">\n'
                        u'  <script type="math/tex; mode=display">%s</script>\n'
                        u'</div>\n\n'),
        '\\[':      (_TeX4Web.cmd_math, '',
                        u'\n<div class="t4w-displaymath math">\n'
                        u'  <script type="math/tex; mode=display">%s</script>\n'
                        u'</div>\n\n'),
        '\\]':      (_TeX4Web.cmd_math, 'err', u''), # XXX

        # Environments
        '\\begin':  (_TeX4Web.cmd_env,),
        '\\end':    (_TeX4Web.cmd_env,),

        # Font commands
        '\\textmd': (_TeX4Web.cmd_group_tag, _span_tag('md')),
        '\\textbf': (_TeX4Web.cmd_group_tag, _span_tag('bf')),

        '\\textrm': (_TeX4Web.cmd_group_tag, _span_tag('rm')),
        '\\textsf': (_TeX4Web.cmd_group_tag, _span_tag('sf')),
        '\\texttt': (_TeX4Web.cmd_group_tag, _span_tag('tt')),

        '\\textup': (_TeX4Web.cmd_group_tag, _span_tag('up')),
        '\\textit': (_TeX4Web.cmd_group_tag, _span_tag('it')),
        '\\textsl': (_TeX4Web.cmd_group_tag, _span_tag('sl')),
        '\\textsc': (_TeX4Web.cmd_group_tag, _span_tag('sc')),
        '\\emph':   (_TeX4Web.cmd_group_tag, _span_tag('em')),
        '\\textnormal': (_TeX4Web.cmd_group_tag, _span_tag('nf')),
        '\\underline':   (_TeX4Web.cmd_group_tag, _span_tag('un')),
        '\\sout':   (_TeX4Web.cmd_group_tag, _span_tag('st')),

        # Font declarations
        '\\mdseries': (_TeX4Web.cmd_group_otag, _span_tag('md')),
        '\\bfseries': (_TeX4Web.cmd_group_otag, _span_tag('bf')),

        '\\rmfamily': (_TeX4Web.cmd_group_otag, _span_tag('rm')),
        '\\sffamily': (_TeX4Web.cmd_group_otag, _span_tag('sf')),
        '\\ttfamily': (_TeX4Web.cmd_group_otag, _span_tag('tt')),

        '\\upshape':  (_TeX4Web.cmd_group_otag, _span_tag('up')),
        '\\itshape':  (_TeX4Web.cmd_group_otag, _span_tag('it')),
        '\\slshape':  (_TeX4Web.cmd_group_otag, _span_tag('sl')),
        '\\scshape':  (_TeX4Web.cmd_group_otag, _span_tag('sc')),
        '\\normalfont': (_TeX4Web.cmd_group_otag, _span_tag('nf')),

        # Font declarations (short forms)
        '\\bf':     (_TeX4Web.cmd_group_otag, _span_tag('bf')),

        '\\rm':     (_TeX4Web.cmd_group_otag, _span_tag('rm')),
        '\\sf':     (_TeX4Web.cmd_group_otag, _span_tag('sf')),
        '\\tt':     (_TeX4Web.cmd_group_otag, _span_tag('tt')),

        '\\it':     (_TeX4Web.cmd_group_otag, _span_tag('it')),
        '\\sl':     (_TeX4Web.cmd_group_otag, _span_tag('sl')),
        '\\sc':     (_TeX4Web.cmd_group_otag, _span_tag('sc')),
        '\\em':     (_TeX4Web.cmd_group_otag, _span_tag('em')),

        # Font sizes
        '\\tiny':   (_TeX4Web.cmd_group_otag, _span_tag('tiny')),
        '\\scriptsize':     (_TeX4Web.cmd_group_otag, _span_tag('scriptsize')),
        '\\footnotesize':   (_TeX4Web.cmd_group_otag, _span_tag('footnotesize')),
        '\\small':  (_TeX4Web.cmd_group_otag, _span_tag('small')),
        '\\normalsize':   (_TeX4Web.cmd_group_otag, _span_tag('normalsize')),
        '\\large':  (_TeX4Web.cmd_group_otag, _span_tag('large')),
        '\\Large':  (_TeX4Web.cmd_group_otag, _span_tag('Large')),
        '\\LARGE':  (_TeX4Web.cmd_group_otag, _span_tag('LARGE')),
        '\\huge':   (_TeX4Web.cmd_group_otag, _span_tag('huge')),
        '\\Huge':   (_TeX4Web.cmd_group_otag, _span_tag('Huge')),

        # Colors
        '\\color':  (_TeX4Web.cmd_color,
                     u'<span class="t4w-color-%s">%s</span>'),
        '\\textcolor':  (_TeX4Web.cmd_textcolor,
                     u'<span class="t4w-color-%s">%s</span>'),

        # Sections
        '\\section':        (_TeX4Web.cmd_section,
                                u'\n<h2 class="t4w-section"'
                                u' id="t4w-section-%s">%s</h2>\n\n',
                                u'<span class="t4w-section-number">%s</span>',
                                u'\n<h2 class="t4w-section-s">%s</h2>\n\n'),
        '\\subsection':     (_TeX4Web.cmd_section,
                                u'\n<h3 class="t4w-subsection"'
                                u' id="t4w-subsection-%s">%s</h3>\n\n',
                                u'<span class="t4w-section-number">%s</span>',
                                u'\n<h3 class="t4w-subsection-s">%s</h3>\n\n'),
        '\\subsubsection':  (_TeX4Web.cmd_section,
                                u'\n<h4 class="t4w-subsubsection"'
                                u' id="t4w-subsubsection-%s">%s</h4>\n\n',
                                u'<span class="t4w-section-number">%s</span>',
                                u'\n<h4 class="t4w-subsubsection-s">%s</h4>\n\n'),

        '\\appendix':       (_TeX4Web.cmd_appendix,),

        # Title
        '\\affiliation':    (_TeX4Web.cmd_title,),
        '\\date':           (_TeX4Web.cmd_title,),
        '\\author':         (_TeX4Web.cmd_title,),
        '\\thanks':         (_TeX4Web.cmd_title,),
        '\\title':          (_TeX4Web.cmd_title,),

        '\\maketitle':      (_TeX4Web.cmd_maketitle,),

        # List items
        '\\item':   (_TeX4Web.cmd_item,
                            u'    <li class="t4w-item">', u'</li>\n',
                            u'<span class="t4w-item-description">%s</span>'),
        '\\bibitem':(_TeX4Web.cmd_bibitem,
                            u'<li class="t4w-bibitem" id="t4w-bibitem-%s">'
                            u'<span class="t4w-bibitem-number">[%s]</span>'
                            u'<span class="t4w-bibitem-backrefs">%s</span>',
                            u'</li>'),

        # References
        '\\cite':   (_TeX4Web.cmd_cite, u'<span class="t4w-cite">[%s]</span>',
                                        u'<a id="%s" href="%s">%s</a>'),
        '\\onlinecite':      (_TeX4Web.cmd_cite, u'<span class="t4w-cite">[%s]</span>',
                                        u'<a id="%s" href="%s">%s</a>'),
        '\\url':    (_TeX4Web.cmd_href, u'<a class="t4w-url" href="%s">%s</a>'),
        '\\href':   (_TeX4Web.cmd_href, u'<a class="t4w-href" href="%s">%s</a>'),
        '\\includegraphics': (_TeX4Web.cmd_includegraphics,
                     u'<img class="t4w-includegraphics" style="%s" src="%s" />'),

        '\\eqref':  (_TeX4Web.cmd_ref,
                    u'<a class="t4w-ref" href="%s">(%s)</a>'),
        '\\ref':    (_TeX4Web.cmd_ref,
                    u'<a class="t4w-ref" href="%s">%s</a>'),
        '\\autoref':    (_TeX4Web.cmd_ref,
                    u'<a class="t4w-autoref" href="%s">%s</a>'),
        '\\label':  (_TeX4Web.cmd_label,),

        '\\caption':(_TeX4Web.cmd_caption,),
    }

    environments = {
        # Section-like environments
        'abstract': (_TeX4Web.env_group_section,
                     u'<div class="t4w-abstract">'
                     u'  <span class="t4w-abstract-title">Abstract:</span>'
                     u'%s</div>'),

        # Group environments
        'center':   (_TeX4Web.env_group,
                     u'<div class="t4w-center">%s</div>'),
        'document': (_TeX4Web.env_group,
                     u'<div>%s</div>'),
        'flushleft':(_TeX4Web.env_group,
                     u'<div class="t4w-flushleft">%s</div>'),
        'flushright':(_TeX4Web.env_group,
                     u'<div class="t4w-flushright">%s</div>'),

        'quotation':(_TeX4Web.env_group,
                     u'\n<div class="t4w-quotation">%s</div>\n\n'),
        'quote':    (_TeX4Web.env_group,
                     u'\n<div class="t4w-quote">%s</div>\n\n'),
        'verse':    (_TeX4Web.env_group,
                     u'\n<div class="t4w-verse">%s</div>\n\n'),

        # Tabular
        'tabular':  (_TeX4Web.env_tabular,
                     u'<table class="t4w-tabular">%s</table>'),
        'table':    (_TeX4Web.env_ngroup,
                     u'<div class="t4w-table">%s'
                     u'<div class="t4w-table-caption">Table %s: %s</div>'
                     u'</div>'),
        'figure':   (_TeX4Web.env_ngroup,
                     u'<div class="t4w-figure">%s'
                     u'<div class="t4w-figure-caption">Figure %s: %s</div>'
                     u'</div>'),

        # Lists
        'description': (_TeX4Web.env_list,
                     u'\n<ul class="t4w-description">\n%s</ul>\n\n'),
        'itemize': (_TeX4Web.env_list,
                     u'\n<ul class="t4w-itemize">\n%s</ul>\n\n'),
        'enumerate': (_TeX4Web.env_list,
                     u'\n<ol class="t4w-enumerate">\n%s</ol>\n\n'),
        'thebibliography': (_TeX4Web.env_thebibliography,
                     u'<div class="t4w-thebibliography">%s'
                     u'<span class="t4w-thebibliography-title">References:</span>'
                     u'<ul>%s</ul></div>'),

        # Math
        'math':     (_TeX4Web.env_math, 
                        u'<span class="t4w-math math">'
                        u'<script type="math/tex">%s</script>'
                        u'</span>'),
        'displaymath': (_TeX4Web.env_math,
                        u'\n<div class="t4w-displaymath math">\n'
                        u'  <script type="math/tex; mode=display">%s</script>\n'
                        u'</div>\n\n'),
        'equation': (_TeX4Web.env_nmath,
                     u'<table class="t4w-equation">\n'
                     u'  <tr>\n'
                     u'    <td class="t4w-equation-math">%s</td>\n'
                     u'    %s\n'
                     u'  </tr>\n'
                     u'</table>',
                     u'\n      <div class="t4w-displaymath math">\n'
                     u'        <script type="math/tex; mode=display">%s</script>\n'
                     u'      </div>\n    ',
                     u'<td class="t4w-equation-number" id="t4w-equation-%s">(%s)</td>'),
        'eqnarray': (_TeX4Web.env_nmath,
                     u'<table class="t4w-eqnarray">\n'
                     u'  <tr>\n'
                     u'    <td class="t4w-eqnarray-math">%s</td>\n'
                     u'    %s\n'
                     u'  </tr>\n'
                     u'</table>',
                     u'\n      <div class="t4w-displaymath math">\n'
                     u'        <script type="math/tex; mode=display">\n'
                     u'          \\begin{array}{}%s\end{array}\n'
                     u'        </script>\n'
                     u'      </div>\n    ',
                     u'<td class="t4w-eqnarray-number" id="t4w-equation-%s">(%s)</td>'
                     ),
        'align': (_TeX4Web.env_nmath,
                     u'<table class="t4w-align">\n'
                     u'  <tr>\n'
                     u'    <td class="t4w-align-math">%s</td>\n'
                     u'    %s\n'
                     u'  </tr>\n'
                     u'</table>',
                     u'\n      <div class="t4w-displaymath math">\n'
                     u'        <script type="math/tex; mode=display">\n'
                     u'           \\begin{array}{}%s\end{array}\n'
                     u'        </script>\n'
                     u'      </div>\n    ',
                     u'<td class="t4w-align-number" id="t4w-equation-%s">(%s)</td>'
                     ),

        # Font declarations
        'mdseries': (_TeX4Web.env_group, _span_tag('md')),
        'bfseries': (_TeX4Web.env_group, _span_tag('bf')),

        'rmfamily': (_TeX4Web.env_group, _span_tag('rm')),
        'sffamily': (_TeX4Web.env_group, _span_tag('sf')),
        'ttfamily': (_TeX4Web.env_group, _span_tag('tt')),

        'upshape':  (_TeX4Web.env_group, _span_tag('up')),
        'itshape':  (_TeX4Web.env_group, _span_tag('it')),
        'slshape':  (_TeX4Web.env_group, _span_tag('sl')),
        'scshape':  (_TeX4Web.env_group, _span_tag('sc')),
        'normalfont': (_TeX4Web.env_group, _span_tag('nf')),

        # Font declarations (short forms)
        'bf':     (_TeX4Web.env_group, _span_tag('bf')),

        'rm':     (_TeX4Web.env_group, _span_tag('rm')),
        'sf':     (_TeX4Web.env_group, _span_tag('sf')),
        'tt':     (_TeX4Web.env_group, _span_tag('tt')),

        'it':     (_TeX4Web.env_group, _span_tag('it')),
        'sl':     (_TeX4Web.env_group, _span_tag('sl')),
        'sc':     (_TeX4Web.env_group, _span_tag('sc')),
        'em':     (_TeX4Web.env_group, _span_tag('em')),
    }
