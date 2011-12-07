## This file is part of Invenio.
## Copyright (C) 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

webdir = $(localstatedir)/www/codemirror

web_DATA = codemirror.js \
           mirrorframe.js \
           parsehtmlmixed.js \
           parsesparql.js \
           stringstream.js \
           tokenize.js \
           util.js \
           editor.js \
           parsecss.js \
           parsejavascript.js \
           parsexml.js \
           styles \
           undo.js \
           highlight.js \
           parsedummy.js \
           parselatex.js \
           select.js \
           tokenizejavascript.js \
           unittests.js

styledir = $(localstatedir)/www/codemirror/styles

style_DATA = latexcolors.css

EXTRA_DIST = $(web_DATA) $(style_DATA)

CLEANFILES = *~ *.tmp
