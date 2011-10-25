previewLive = true;
var previewUpdateTimeMin = 60;
var previewUpdateTimeMax = 3000;
var previewUpdateTime = 0;
var previewTimer = undefined;
var editor = {};
var tex4web = undefined;

var parts = new Array();

function strReplace(str, replace, by)
{
    for (var i=0; i<replace.length; i++)
        str = str.replace(RegExp(replace[i], 'g'), by[i]);
    return str;
}

function html_to_tex(str)
{
    //This function was first added for INVENIO
    var allowed_tags = '<a><br><ul><ol><li><hr><strong><b><em><i><u><strike><sup><sub><blockqoute><img>';
    var tags_re = /<\/?([a-z][a-z0-9]*)\b[^>]*>/gi;
    str = str.replace(tags_re, function($0, $1){
        return allowed_tags.indexOf('<' + $1.toLowerCase() + '>') > -1 ? $0 : '';
    });
    str = '<html>' + str + '</html>';
    str = strReplace(str, Array('<br />', '<ul>', '</ul>', '<ol>', '</ol>', '<li>', '</li>', '<hr />'), Array("\n", '\\begin{itemize}', '\\end{itemize}', '\\begin{enumerate}', '\\end{enumerate}', '\\item', '', '\\rule{width}{thickness}'));
    var tag = /(<\/?[a-z][a-z0-9]*)\b(?:[^>]*((?:href|src)="[^"]*"))?[^>]*?(\/)?>/;
    parts = str.split(tag);
    var result = finalize_tex(0, 0);
    str = result[0];
    str = strReplace(str, Array( '&euro;', '&iexcl;', '&cent;', '&pound;', '&curren;', '&yen;', '&brvbar;', '&sect;', '&copy;', '&ordf;', '&reg;', '&macr;', '&para;', '&middot;', '&ordm;', '&iquest;', '&ETH;', '&sbquo;', '&bdquo;', '&hellip;', '&trade;', '&rarr;', '&rArr;', '&hArr;', '&diams;', '&THORN;', '&thorn;', '&upsih;', '&prime;', '&Prime;', '&lowast;', '&frasl;', '&larr;', '&uarr;', '&darr;', '&harr;', '&crarr;', '&lArr;', '&uArr;', '&dArr;', '&Alpha;', '&Beta;', '&Gamma;', '&Delta;', '&Epsilon;', '&Zeta;', '&Eta;', '&Theta;', '&Iota;', '&Kappa;', '&Lambda;', '&Mu;', '&Nu;', '&Xi;', '&Omicron;', '&Pi;', '&Rho;', '&Sigma;', '&Tau;', '&Upsilon;', '&Phi;', '&Chi;', '&Psi;', '&Omega;', '&alpha;', '&beta;', '&gamma;', '&delta;', '&epsilon;', '&zeta;', '&eta;', '&theta;', '&iota;', '&kappa;', '&lambda;', '&mu;', '&nu;', '&xi;', '&omicron;', '&pi;', '&rho;', '&sigmaf;', '&sigma;', '&tau;', '&upsilon;', '&phi;', '&chi;', '&psi;', '&omega;', '&thetasym;', '&piv;', '&image;', '&real;', '&alefsym;', '&weierp;', '&part;', '&exist;', '&empty;', '&nabla;', '&isin;', '&notin;', '&ni;', '&prod;', '&sum;', '&minus;', '&radic;', '&infin;', '&prop;', '&ang;', '&and;', '&or;', '&cap;', '&cup;', '&int;', '&there4;', '&sim;', '&cong;', '&asymp;', '&ne;', '&equiv;', '&le;', '&ge;', '&sub;', '&sup;', '&bull;', '&sube;', '&supe;', '&nsub;', '&oplus;', '&otimes;', '&perp;', '&sdot;', '&lceil;', '&rceil;', '&lfloor;', '&rfloor;', '&lang;', '&rang;', '&loz;', '&cedil;', '&sup1;', '&frac14;', '&frac12;', '&frac34;', '&Agrave;', '&Aacute;', '&Acirc;', '&Atilde;', '&Auml;', '&Aring;', '&AElig;', '&Ccedil;', '&Egrave;', '&Eacute;', '&Ecirc;', '&Euml;', '&Igrave;', '&Iacute;', '&Icirc;', '&Iuml;', '&Ntilde;', '&Ograve;', '&Oacute;', '&Ocirc;', '&Otilde;', '&Ouml;', '&times;', '&Oslash;', '&Ugrave;', '&Uacute;', '&Ucirc;', '&Uuml;', '&Yacute;', '&THORN;', '&szlig;', '&agrave;', '&aacute;', '&acirc;', '&atilde;', '&auml;', '&aring;', '&aelig;', '&ccedil;', '&egrave;', '&eacute;', '&ecirc;', '&euml;', '&igrave;', '&iacute;', '&icirc;', '&iuml;', '&eth;', '&ntilde;', '&ograve;', '&oacute;', '&ocirc;', '&otilde;', '&ouml;', '&divide;', '&oslash;', '&ugrave;', '&uacute;', '&ucirc;', '&uuml;', '&yacute;', '&thorn;', '&yuml;', '&OElig;', '&oelig;', '&Wcirc;', '&Ycirc;', '&wcirc;', '&ycirc;', '&fnof;', '&forall;', '&micro;', '&acute;', '&sup3;', '&sup2;', '&deg;', '&not;', '&raquo;', '&laquo;', '&uml;', '&ndash;', '&mdash;', '&rdquo;', '&ldquo;', '&rsquo;', '&lsquo;', '&lt;', '&gt;', '&quot;', '&#39;', '&nbsp;', '&amp;'), Array( '{\\texteuro}', '!`', '{\\textcent}', '{\\pounds}', '{\\textcurrency}', '{\\textyen}', '{\\splitvert}', '{\\S}', '{\\copyright}', '{\\textordfeminine}', '{\\textregistered}', '$##{^-}##$', '{\\P}', '{\\cdot}', '{\\textordmasculine}', '?`', '{\\DH}', '{\\textquotestraightbase}', '{\\textquotestraightdblbase}', '{\\dots}', '{\\texttrademark}', '{\\rightarrow}', '{\\Rightarrow}', '{\\Leftrightarrow}', '{\\blackdiamond}', '{\\Thorn}', '{\\thorn}', '$##\\Upsilon##$', '{\\prime}', '{\\second}', '{\\textasteriskcentered}', '{\\diagup}', '{\\leftarrow}', '{\\uparrow}', '{\\downarrow}', '{\\leftrightarrow}', '{\\dlsh}', '{\\Leftarrow}', '{\\Uparrow}', '{\\Downarrow}', 'A', 'B', '$##\\Gamma##$', '$##\\Delta##$', 'E', 'Z', 'H', '$##\\Theta##$', 'I', 'K', '$##\\Lambda##$', 'M', 'N', '$##\\Xi##$', 'O', '$##\\Pi##$', 'P', '$##\\Sigma##$', 'T', 'Y', '$##\\Phi##$', 'X', '$##\\Psi##$', '$##\\Omega##$', '$##\\alpha##$', '$##\\beta##$', '$##\\gamma##$', '$##\\delta##$', '$##\\epsilon##$', '$##\\zeta##$', '$##\\eta##$', '$##\\theta##$', '$##\\iota##$', '$##\\kappa##$', '$##\\lambda##$', '$##\\mu##$', '$##\\nu##$', '$##\\xi##$', '$##\\omicron##$', '$##\\pi##$', '$##\\rho##$', '$##\\varsigma##$', '$##\\sigma##$', '$##\\tau##$', '$##\\upsilon##$', '$##\\varphi##$', '$##\\chi##$', '$##\\psi##$', '$##\\omega##$', '$##\\vartheta##$', '$##\\varpi##$', '$##\\Im##$', '$##\\Re##$', '$##\\aleph##$', '$##\\wp##$', '$##\\partial##$', '$##\\exists##$', '{\\O}', '$##\\nabla##$', '$##\\in##$', '$##\\notin##$', '$##\\ni##$', '$##\\prod##$', '$##\\sum##$', '--', '$##\\sqrt{}##$', '$##\\infty##$', '$##\\propto##$', '$##\\angle##$', '$##\\wedge##$', '$##\\vee##$', '$##\\cap##$', '$##\\cup##$', '$##\\int##$', '$##\\therefore##$', '$##\\sim##$', '$##\\cong##$', '$##\\approx##$', '$##\\ne##$', '$##\\equiv##$', '$##\\le##$', '$##\\ge##$', '$##\\subset##$', '$##\\supset##$', '$##\\bullet##$', '$##\\subseteq##$', '$##\\supseteq##$', '$##\\not\\subset##$', '$##\\oplus##$', '$##\\otimes##$', '$##\\perp##$', '$##\\cdot##$', '$##\\lceil##$', '$##\\rceil##$', '$##\\lfloor##$', '$##\\rfloor##$', '$##\\langle##$', '$##\\rangle##$', '$##\\diamondsuit##$', '\\c{}', '$##{^1}##$', '$##\\frac14##$', '$##\\frac12##$', '$##\\frac34##$', '\\`A', '\\\'A', '\\^A', '\\~A', '\\"A', '{\\AA}', '{\\AE}', '\\c C', '\\`E', '\\\'E', '\\^E', '\\"E', '\\`I', '\\\'I', '\\^I', '\\"I', '\\~N', '\\`O', '\\\'O', '\\^O', '\\~O', '\\"O', '$##\\times##$', '{\\O}', '\\`U', '\\\'U', '\\^U', '\\"U', '\\`Y', 'P', '{\\ss}', '\\`a', '\\\'a', '\\^a', '\\~a', '\\"a', '{\\aa}', '{\\ae}', '\\c c', '\\`e', '\\\'e', '\\^e', '\\"e', '\\`i', '\\\'i', '\\^i', '\\"i', '{\\dh}', '\\~n', '\\`o', '\\\'o', '\\^o', '\\~o', '\\"o', '$##\\div##$', '{\\o}', '\\`u', '\\\'u', '\\^u', '\\"u', '\\`y', 'p', '\\"y', '{\\OE}', '{\\oe}', '\\^W', '\\^Y', '\\^w', '\\^y', '\\textit{f}', '$##\\forall##$', '$##\\mu##$', '\\\'{}', '$##{^3}##$', '$##{^2}##$', '$##^\\circ##$', '$##\\neg##$', '$##\\gg##$', '$##\\ll##$', '\\"{}', '--', '---', '{\\textquotedblright}', '{\\textquotedblleft}', '{\\textquoteright}', '{\\textquoteleft}', '<', '>', '"', "'", ' ', '&'));
    str = str.replace(/##\$\$##/g, "");
    str = str.replace(/##\$/g, "$");
    str = str.replace(/\$##/g, "$");
    str = str.replace(/\n\n/g, "\n");
    return str;
}

function open_tag(tag, href)
{
    var result = Array('', 0);
    if (typeof(href) == "undefined")
    {
        href = '';
    }
    switch (tag)
    {
        case 'a':
            result[1] = 1;
            result[0] = '\\href{' + href.slice(6,-1) + '}{';
            break;
        case 'strong':
        case 'b':
            result[1] = 1;
            result[0] = '\\textbf{';
            break;
        case 'em':
        case 'i':
            result[1] = 1;
            result[0] = '\\textit{';
            break;
        case 'strike':
            result[1] = 1;
            result[0] = '\\sout{';
            break;
        case 'u':
            result[1] = 1;
            result[0] = '\\underline{';
            break;
        case 'blockquote':
            result[1] = 1;
            result[0] = "\\begin{quote}\n";
            break;
        case 'img':
            result[1] = 0;
            result[0] = '\\includegraphics{' + href.slice(5, -1) + '}';
            break;
        case 'sup':
            result[1] = 2;
            result[0] = '$^{';
            break;
        case 'sub':
            result[1] = 2;
            result[0] = '$_{';
            break;
    }
    return result;
}

function close_tag(tag)
{
    switch (tag)
    {
        case 'a':
        case 'strong':
        case 'b':
        case 'em':
        case 'i':
        case 'strike':
        case 'u':
            return '}';
            break;
        case 'blockquote':
            return "\\\nend{quote}";
            break;
        case 'img':
            return '';
            break;
        case 'sup':
        case 'sub':
            return "}$";
            break;
    }
    return '';
}

function finalize_tex(offset, escape_type)
{
    var final_str = '';
    while(offset < parts.length)
    {
        if (typeof(parts[offset]) == "undefined" || parts[offset] == "")
        {
            offset++;
            continue;
        }
        if (parts[offset][0] == '<')
        {
            if (parts[offset][1] == '/')
            {
                final_str += close_tag(parts[offset].substr(2));
                return Array(final_str, offset+3);
            }

            var result = open_tag(parts[offset].substr(1), parts[offset+1]);
            final_str += result[0];
            if (typeof(parts[offset+2]) != "undefined")
            {
                final_str += close_tag(parts[offset].substr(1));
                offset += 3;
            }
            else
            {
                result = finalize_tex(offset+3, (result[1] < escape_type) ? escape_type : result[1]);
                final_str += result[0];
                offset = result[1];
            }
        }
        else
        {
            if (escape_type > 0)
            {
                parts[offset] = parts[offset].replace(/{/g, '\\{');
                parts[offset] = parts[offset].replace(/}/g, '\\}');
                parts[offset] = parts[offset].replace(/\\/g, '\\\\');
                parts[offset] = parts[offset].replace(/\$/g, '\\$');
            }
            if (escape_type > 1)
            {
                parts[offset] = parts[offset].replace(/\$/g, '\\$');
            }
            final_str += parts[offset];
            offset++;
        }
    }
    return Array(final_str, offset);
}

function make_preview() {
    if(!window.TeX4WebSW) {
        previewUpdateTime = 500;
        make_preview_delayed();
        return;
    }

    if(!tex4web)
        tex4web = window.TeX4WebSW(documentUrl);

    var startTime = new Date().getTime();

    var text = editor.inputElement.value;
    if(text == editor.oldText) { return; }
    editor.oldText = text;

    text = tex4web.parse_document(text);

    editor.previewElement.innerHTML = text;

    var anchors = editor.previewElement.getElementsByTagName('A');
    var i = 0;
    for(i = 0; i < anchors.length; i++) {
        if(anchors[i].href.substr(0,1) != '#' &&
                anchors[i].href.substr(0,location.href.length+1) !=
                    location.href+'#') {
            anchors[i].target = '_blank';
        }
    }

    MathJax.Hub.Queue(["Typeset", MathJax.Hub, editor.previewElement]);

    var endTime = new Date().getTime();
    previewUpdateTime = endTime - startTime;
    return;
}

function make_preview_delayed() {
    if(previewTimer) {
        clearTimeout(previewTimer);
        previewTimer = undefined;
    }

    var timeout = previewUpdateTime;
    if(timeout < previewUpdateTimeMin)
       timeout = 0;
    else if(timeout > previewUpdateTimeMax)
       timeout = previewUpdateTimeMax;

    previewTimer = setTimeout(make_preview, timeout);
}

function live_preview_enable() {
    $('.m-editor-editor-content textarea')
        .keypress(make_preview_delayed)
        .keydown(make_preview_delayed)
        .bind('paste', make_preview_delayed)
        .bind('drop', make_preview_delayed);

    make_preview();
    $('#m-editor-live-on').addClass('text-button-selected');
    $('#m-editor-live-off').removeClass('text-button-selected');
}

function live_preview_disable() {
    $('.m-editor-editor-content textarea').unbind();
    $('#m-editor-live-on').removeClass('text-button-selected');
    $('#m-editor-live-off').addClass('text-button-selected');
}

function _setup_resizer_h() {
    $('#m-editor-resizer').resizable({
        minHeight: 300, handles: 's',
        alsoResize: '.m-editor-block-resizer',
        stop: function() {
            $('#m-editor-resizer')
                .css({height: 'auto'});
        }
    });
}

function _destroy_resizer_h() {
    $('#m-editor-resizer').resizable('destroy')
        .css({height: 'auto'});
    $('.m-editor-block-resizer')
        .css({height: '400px', width: '100%'});
}

function _setup_resizer_v() {
    $('.m-editor-block-resizer').resizable({
        minHeight: 150, handles: 's'
    });
}

function _destroy_resizer_v() {
    $('.m-editor-block-resizer').resizable('destroy')
        .css({height: '400px'});
}

function layout_set_vertical() {
    _destroy_resizer_h();

    $('.m-editor-inner').css('width', '100%');
    $('.m-editor-block-options').css('margin-right', '50%');
    $('#m-editor-layout-vertical').addClass('text-button-selected');
    $('#m-editor-layout-horizontal').removeClass('text-button-selected');

    _setup_resizer_v();
}

function layout_set_horizontal() {
    _destroy_resizer_v();

    $('.m-editor-inner').css('width', '50%');
    $('.m-editor-block-resizer').css('width', '100%');
    $('.m-editor-block-options').removeAttr('style');
    $('#m-editor-layout-vertical').removeClass('text-button-selected');
    $('#m-editor-layout-horizontal').addClass('text-button-selected');

    _setup_resizer_h();
}

$(document).ready(function() {
    if ($('#id_content').length == 0)
        return;
    editor.panels = {};
    editor.inputElement = $('.m-editor-editor-content textarea')[0];
    editor.previewElement = $('.m-editor-preview-content div')[0];

    live_preview_enable();

    $('#id_content_form_submit').click(function() {
        $('#id_content_form').submit();
    });
    $('#id_content_form_cancel').click(function() {
        location.href = cancelUrl;
    });
    $('#id_content_form_publish').click(function() {
        if ($('#id_is_public').val()=='True')
            $('#id_is_public').val('False');
        else
            $('#id_is_public').val('True');
        $('#id_content_form').submit();
    });

    $('#m-editor-layout-vertical').click(function() {
        this.blur(); layout_set_vertical(); return false; });
    $('#m-editor-layout-horizontal').click(function() {
        this.blur(); layout_set_horizontal(); return false; });

    $('#m-editor-live-on' ).click(function() {
        this.blur(); live_preview_enable(); return false; });
    $('#m-editor-live-off').click(function() {
        this.blur(); live_preview_disable(); return false; });
    $('#m-editor-live-update').click(function() {
        this.blur(); make_preview(); return false; });

    _setup_resizer_h();
});
