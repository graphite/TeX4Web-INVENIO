# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Invenio.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
BibDocAdmin CLI administration tool
"""

__revision__ = "$Id$"

from optparse import OptionParser, OptionGroup
from invenio.bibdocfile import BibRecDocs, BibDoc, InvenioWebSubmitFileError, \
    nice_size
from invenio.intbitset import intbitset
from invenio.search_engine import perform_request_search
from invenio.textutils import wrap_text_in_a_box, wait_for_user
from invenio.dbquery import run_sql

def _xml_mksubfield(key, subfield, fft):
    return fft.has_key(key) and '\t\t<subfield code="a">%s</subfield>\n' % fft[key] or ''

def _xml_fft_creator(fft):
    """Transform an fft dictionary (made by keys url, docname, format,
    new_docname, icon, comment, description, restriction, doctype, into an xml
    string."""
    out = '\t<datafield tag ="FFT" ind1=" " ind2=" ">\n'
    out += _xml_mksubfield('url', 'a', fft)
    out += _xml_mksubfield('docname', 'n', fft)
    out += _xml_mksubfield('format', 'f', fft)
    out += _xml_mksubfield('newdocname', 'm', fft)
    out += _xml_mksubfield('doctype', 't', fft)
    out += _xml_mksubfield('description', 'd', fft)
    out += _xml_mksubfield('comment', 'c', fft)
    out += _xml_mksubfield('restriction', 'r', fft)
    out += _xml_mksubfield('icon', 'x', fft)
    out += '\t</datafield>'
    return out

def ffts_to_xmls(ffts):
    """Transform a dictionary: recid -> ffts where ffts is a list of fft dictionary
    into xml.
    """
    out = ''
    for recid, ffts in ffts.iteritems():
        out += '<record>\n'
        out += '\t<controlfield tag="001">%i</controlfield>\n' % recid
        for fft in ffts:
            out += _xml_fft_creator(fft)
        out += '</record>\n'
    return out

def get_usage():
    """Return a nicely formatted string for printing the help of bibdocadmin"""
    return """usage: %prog <query> <action> [options]
  <query>: --pattern <pattern>, --collection <collection>, --recid <recid>,
           --recid2 <recid>, --doctype <doctype>, --docid <docid>,
           --docid2 <docid>, --docname <docname>, --revision <revision>,
           --format <format>, --url <url>,
 <action>: --get-info, --get-stats, --get-usage, --get-docnames
           --get-docids, --get-recids, --get-doctypes, --get-revisions,
           --get-last-revisions, --get-formats, --get-comments,
           --get-descriptions, --get-restrictions, --get-icons,
           --get-history,
           --delete, --undelete, --purge, --expunge, --revert <revision>,
           --check-md5, --update-md5,
           --set-doctype <doctype>, --set-docname <docname>,
           --set-comment <comment>, --set-description <description>,
           --set-restriction <tag>, --set-icon <path>,
           --append <path>, --revise <path>,
[options]: --with-stamp-template <template>, --with-stamp-parameters <parameters>,
           --verbose <level>, --force, --interactive, --with-icon-size <size>,
           --with-related-formats
With <query> you select the range of record/docnames/single files to work on.
Note that some actions e.g. delete, append, revise etc. works at the docname
level, while others like --set-comment, --set-description, at single file level
and other can be applied in an iterative way to many records in a single run.

Note that specifing docid(2) takes precedence over recid(2) which in turns
takes precedence over pattern/collection search.
"""

_actions = ['get-info',
            #'get-stats',
            'get-usage',
            'get-docnames',
            #'get-docids',
            #'get-recids',
            #'get-doctypes',
            #'get-revisions',
            #'get-last-revisions',
            #'get-formats',
            #'get-comments',
            #'get-descriptions',
            #'get-restrictions',
            #'get-icons',
            'get-history',
            #'delete',
            #'undelete',
            #'purge',
            #'expunge',
            'check-md5',
            'update-md5']

_actions_with_parameter = {
    #'set-doctype' : 'doctype',
    #'set-docname' : 'docname',
    #'set-comment' : 'comment',
    #'set-description' : 'description',
    #'set-restriction' : 'restriction',
    #'append' : 'append_path',
    #'revise' : 'revise_path',
}

def prepare_option_parser():
    """Parse the command line options."""
    parser = OptionParser(usage="usage: %prog <query> <action> [options]",
    epilog="""With <query> you select the range of record/docnames/single files to work on.
Note that some actions e.g. delete, append, revise etc. works at the docname
level, while others like --set-comment, --set-description, at single file level
and other can be applied in an iterative way to many records in a single run.

Note that specifing docid(2) takes precedence over recid(2) which in turns
takes precedence over pattern/collection search.""",
 version=__revision__)
    query_options = OptionGroup(parser, 'Query parameters')
    query_options.add_option('-p', '--pattern', dest='pattern')
    query_options.add_option('-c', '--collection', dest='collection')
    query_options.add_option('-r', '--recid', type='int', dest='recid')
    query_options.add_option('--recid2', type='int', dest='recid2')
    query_options.add_option('-d', '--docid', type='int', dest='docid')
    query_options.add_option('--docid2', type='int', dest='docid2')
    query_options.add_option('--docname', dest='docname')
    query_options.add_option('--url', dest='url')
    query_options.add_option('--revision', dest='revision', default='last')
    query_options.add_option('--format', dest='format')
    parser.add_option_group(query_options)
    action_options = OptionGroup(parser, 'Actions')
    for action in _actions:
        action_options.add_option('--%s' % action, action='store_const', const=action, dest='action')
    parser.add_option_group(action_options)
    action_with_parameters = OptionGroup(parser, 'Actions with parameter')
    for action, dest in _actions_with_parameter.iteritems():
        action_with_parameters.add_option('--%s' % action, dest=dest)
    #parser.add_option_group(action_with_parameters)
    parser.add_option('-v', '--verbose', type='int', dest='verbose', default=1)
    return parser

def get_recids_from_query(pattern, collection, recid, recid2, docid, docid2):
    """Return the proper set of recids corresponding to the given
    parameters."""
    if docid:
        ret = intbitset()
        if not docid2:
            docid2 = docid
        for adocid in xrange(docid, docid2 + 1):
            try:
                bibdoc = BibDoc(adocid)
                if bibdoc and bibdoc.get_recid():
                    ret.add(bibdoc.get_recid())
            except (InvenioWebSubmitFileError, TypeError):
                pass
        return ret
    elif recid:
        if not recid2:
            recid2 = recid
        recid_range = intbitset(xrange(recid, recid2 + 1))
        recid_set = intbitset(run_sql('select id from bibrec'))
        recid_set &= recid_range
        return recid_set
    elif pattern or collection:
        return intbitset(perform_request_search(cc=collection, p=pattern))
    else:
        return intbitset(run_sql('select id from bibrec'))

def get_docids_from_query(recid_set, docid, docid2):
    """Given a set of recid and an optional range of docids
    return a corresponding docids set. The range of docids
    takes precedence over the recid_set."""
    if docid:
        ret = intbitset()
        if not docid2:
            docid2 = docid
        for adocid in xrange(docid, docid2 + 1):
            try:
                bibdoc = BibDoc(adocid)
                if bibdoc:
                    ret.add(adocid)
            except (InvenioWebSubmitFileError, TypeError):
                pass
        return ret
    else:
        ret = intbitset()
        for recid in recid_set:
            bibrec = BibRecDocs(recid)
            for bibdoc in bibrec.list_bibdocs():
                ret.add(bibdoc.get_id())
                icon = bibdoc.get_icon()
                if icon:
                    ret.add(icon.get_id())
        return ret

def print_info(recid, docid, info):
    """Nicely print info about a recid, docid pair."""
    print '%i:%i:%s' % (recid, docid, info)

def cli_get_history(docid_set):
    """Print the history of a docid_set."""
    print wrap_text_in_a_box(title="BibDocs history", style='conclusion'),
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        history = bibdoc.get_history()
        for row in history:
            print_info(bibdoc.get_recid(), docid, row)

def cli_get_info(recid_set):
    """Print all the info of a recid_set."""
    print wrap_text_in_a_box(title="BibRecDocs info", style='conclusion'),
    for recid in recid_set:
        print BibRecDocs(recid)

def cli_get_docnames(docid_set):
    """Print all the docnames of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        print_info(bibdoc.get_recid(), docid, bibdoc.get_docname())

def cli_get_usage(docid_set):
    """Print the space usage of a docid_set."""
    total_size = 0
    total_latest_size = 0
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        size = bibdoc.get_total_size()
        total_size += size
        latest_size = bibdoc.get_total_size_latest_version()
        total_latest_size += latest_size
        print_info(bibdoc.get_recid(), docid, 'size %s, latest version size %s' % (nice_size(size), nice_size(total_latest_size)))
    print wrap_text_in_a_box('total size: %s\n\nlatest version total size: %s'
        % (nice_size(total_size), nice_size(total_latest_size)),
        style='conclusion')

def cli_check_md5(docid_set):
    """Check the md5 sums of a docid_set."""
    failures = 0
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        if bibdoc.md5s.check():
            print_info(bibdoc.get_recid(), docid, 'checksum OK')
        else:
            for afile in bibdoc.list_all_files():
                if not afile.check():
                    failures += 1
                    print_info(bibdoc.get_recid(), docid, '%s failing checksum!' % afile.get_full_path())
    if failures:
        print wrap_text_in_a_box('%i files failing' % failures , style='conclusion')
    else:
        print wrap_text_in_a_box('All files are correct', style='conclusion')

def cli_update_md5(docid_set):
    """Update the md5 sums of a docid_set."""
    for docid in docid_set:
        bibdoc = BibDoc(docid)
        if bibdoc.md5s.check():
            print_info(bibdoc.get_recid(), docid, 'checksum OK')
        else:
            for afile in bibdoc.list_all_files():
                if not afile.check():
                    print_info(bibdoc.get_recid(), docid, '%s failing checksum!' % afile.get_full_path())
            wait_for_user('Updating the md5s of this document can hide real problems.')
            bibdoc.md5s.update(only_new=False)

def main():
    parser = prepare_option_parser()
    (options, args) = parser.parse_args()
    recid_set = get_recids_from_query(options.pattern, options.collection, options.recid, options.recid2, options.docid, options.docid2)
    docid_set = get_docids_from_query(recid_set, options.docid, options.docid2)
    if options.action == 'get-history':
        cli_get_history(docid_set)
    elif options.action == 'get-info':
        cli_get_info(recid_set)
    elif options.action == 'get-docnames':
        cli_get_docnames(docid_set)
    elif options.action == 'get-usage':
        cli_get_usage(docid_set)
    elif options.action == 'check-md5':
        cli_check_md5(docid_set)
    elif options.action == 'update-md5':
        cli_update_md5(docid_set)

if __name__=='__main__':
    main()