/**
 *
 * This file contains javascript extensions for Jupyter notebook,
 * compatible with Jupyter. The file contains the following extensions
 *
 * a. Button to launch QTConsole
 * b. Button to show/hide all input cells
 * c. Toolbar entry to add show/hide checkbox for each cell
 * d. Hide all marked cells when Notebook is launched
 * e. Open gVim to edit current cell and update with saved content
 * f. Increase/Decrease input code size
 * g. Show line numbers by deafult
 *
 * Other settings:
 * i.  Show line numbers by default in code cells
 * ii. Show equation number when using Mathjax
 *
 * Ben Varkey Benjamin :
 * 21-Mar-2015 : First version
 * 16-Apr-2015 : Added +/- for input code size
 * 29-Oct-2015 : Remove code-folding (available in nbextensions)
 *               Updated to work with Jupyter 4
 */

/*
 * Code to hide the raw code
 * ref:
 * [1] http://blog.nextgenetics.net/?e=102
 */
code_show=true; 
function code_toggle() {
    if (code_show){
        $('div.input').hide();
    } else {
        $('div.input').show();
    }
    code_show = !code_show;
} 

function code_change_fontsize(doIncrease) {
    var pre_css = null;
    var pre_style = null;
    for(i = 0; i < document.styleSheets.length; i++){
        if(/localhost.*\/custom\/custom\.css/.test(document.styleSheets[i].href)){ //if style sheet is custom.css
            pre_css = document.styleSheets[i]; //pre_css now contains the style sheet custom.css
            break;
        }
    }

    for(i = 0; i < pre_css.cssRules.length; i++){
        if(/\.CodeMirror pre/.test(pre_css.cssRules[i].selectorText)){
            pre_style = pre_css.cssRules[i].style;
            break;
        }
    }

    if(pre_style == null){
        pre_css.insertRule(".CodeMirror pre { font-size: \"14px\"; padding-bottom: \"0px\"; }", 0);
        pre_style = pre_css.cssRules[0];
    }

    var font_size = pre_style.fontSize;
    if(font_size == "")
        font_size = 14;
    else
        font_size = +/\d+/.exec(font_size)[0];
    font_size += (doIncrease ? +3 : -3);
    font_size = (font_size < 8 ? 8 : font_size);
    var padding_size = (font_size <= 14 ? 0 : (font_size - 14));

    pre_style.paddingBottom = padding_size + "px";
    pre_style.fontSize = font_size + "px";
}

define([
    'base/js/namespace',
    'base/js/events'
    ], function(Jupyter, events) {
        events.on("app_initialized.NotebookApp", function () {
            Jupyter.toolbar.add_buttons_group([
                /**
                 * a. Button to launch QTConsole
                 */
                {
                     'label'   : 'Run QTConsole',
                     'icon'    : 'fa-terminal', // select your icon from http://fortawesome.github.io/Font-Awesome/icons
                     'callback': function () {
                         Jupyter.notebook.kernel.execute('%qtconsole')
                     }
                },
                /*
                 * b. Button to show/hide all input cells
                 */
                {
                     'label'   : 'Toggle Code',
                     'icon'    : 'fa-code', // select your icon from http://fortawesome.github.io/Font-Awesome/icons
                     'callback': function () {
                        $( document ).ready(code_toggle);
                     }
                },
                /*
                 * f. Button to increase/decrease code font size
                 */
                {
                     'label'   : 'Increase code font size',
                     'icon'    : 'fa-search-plus',
                     'callback': function () {
                        $( document ).ready(code_change_fontsize(true));
                     }
                },
                {
                     'label'   : 'Decrease code font size',
                     'icon'    : 'fa-search-minus',
                     'callback': function () {
                        $( document ).ready(code_change_fontsize(false));
                     }
                }
                
            ]);
            /*
             * c. Toolbar entry to add show/hide checkbox for each cell
             */
            var CellToolbar = Jupyter.CellToolbar;
            var show_hide_input = CellToolbar.utils.checkbox_ui_generator('Hide Input',
             // setter
             function(cell, value){
                 // we check that the _draft namespace exist and create it if needed
                 if (cell.metadata._ben == undefined){cell.metadata._ben = {};}
                    // set the value
                 cell.metadata._ben.show_hide_input = value;
                 if(value === true){
                    cell.element.children()[0].childNodes[1].childNodes[1].style.display="none";
                 }else if(value === false){
                    cell.element.children()[0].childNodes[1].childNodes[1].style.display="block";
                 }},
             //getter
             function(cell){ var ns = cell.metadata._ben;
                 // if the _draft namespace does not exist return undefined
                 // (will be interpreted as false by checkbox) otherwise
                 // return the value
                    return (ns == undefined)? undefined: ns.show_hide_input;
                 }
             );
            CellToolbar.register_callback('show_hide_input.chkb', show_hide_input);
            CellToolbar.register_preset('Show/Hide Input', ['show_hide_input.chkb']);
            /* 
             * e. Open gVim to edit current cell and update with saved content 
             * Use 'g' to open gvim. Use 'u' after saving and exiting gvim.
             *
             * I think I found this code on some Stackoverflow page.
             *
             */
            Jupyter.keyboard_manager.command_shortcuts.add_shortcut('g', {
                handler : function (event) {
                    var input = Jupyter.notebook.get_selected_cell().get_text();
                    var cmd = "f = open('/tmp/.ipycell.py', 'w');f.close()";
                    if (input != "") {
                        cmd = '%%writefile /tmp/.ipycell.py\n' + input;
                    }
                    Jupyter.notebook.kernel.execute(cmd);
                    cmd = "import os;os.system('gvim /tmp/.ipycell.py')";
                    Jupyter.notebook.kernel.execute(cmd);
                    return false;
                }}
            );
            Jupyter.keyboard_manager.command_shortcuts.add_shortcut('u', {
                handler : function (event) {
                    function handle_output(msg) {
                        var ret = msg.content.text;
                        Jupyter.notebook.get_selected_cell().set_text(ret);
                    }
                    var callback = {'output': handle_output};
                    var cmd = "f = open('/tmp/.ipycell.py', 'r');print(f.read())";
                    Jupyter.notebook.kernel.execute(cmd, {iopub: callback}, {silent: false});
                    return false;
                }}
            );
            // g. Show line numbers by default
            Jupyter.CodeCell.options_default.cm_config["lineNumbers"] = true;
        });
});

/* 
 * d. Hide all marked cells when Notebook is launched
 * 
 * Ref: http://nbviewer.ipython.org/github/Carreau/posts/blob/master/04-initialisation-cell.ipynb
 */
var hide_init = function(){
    var cells = Jupyter.notebook.get_cells();
    for(var i in cells){
        var cell = cells[i];
        var namespace =  cell.metadata._ben|| {};
        var isHidden = namespace.show_hide_input;
        // you also need to check that cell is instance of code cell,
        // but lets keep it short
        if( isHidden === true){
            cell.element.children()[0].childNodes[1].childNodes[1].style.display="none";
        }
    }
};
$([Jupyter.events]).on('notebook_loaded.Notebook', hide_init);
