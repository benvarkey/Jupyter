
define([
    'base/js/namespace',
    'base/js/events',
    'codemirror/keymap/vim'
    ], function(Jupyter, events) {
        events.on("app_initialized.NotebookApp", function () {
            code_show=true; 
            function code_toggle() {
                if (code_show){
                    $('div.input').hide('slow');
                } else {
                    $('div.input').show('slow');
                }
                code_show = !code_show;
            } 
            Jupyter.toolbar.add_buttons_group([
                {
                    'id'       : 'toggle_input_cells',
                     'label'   : 'Toggle Code',
                     'icon'    : 'fa-code', // select your icon from http://fortawesome.github.io/Font-Awesome/icons
                     'callback': function () {
                        $( document ).ready(code_toggle);
                     }
                }
            ]);
            // Enable line numbers by default
            Jupyter.CodeCell.options_default.cm_config["lineNumbers"] = true;
            CodeMirror.Vim.map("jj","<Esc>","insert");
            console.log('*customizations loaded*');
        });
});
