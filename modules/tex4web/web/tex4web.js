previewLive = true;
var previewUpdateTimeMin = 60;
var previewUpdateTimeMax = 3000;
var previewUpdateTime = 0;
var previewTimer = undefined;
var editor = {};
var tex4web = undefined;

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
