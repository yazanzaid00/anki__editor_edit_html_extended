- `Format code after closing (minify/compact)` (default is "true") If true the html source code of a field of a note will be processed with the python package htmlmin. To leave the code unchanged set this config key to false.
- `Format code before opening (unfold)` (default is "bs4-prettified"). "bs4-prettified" means that the html is formatted by the "pretty" function of the python module beautifulsoup4. Other possible values are false (then the html source code is not processed) or "tweaked". "tweaked" means that the code from luoliyan's add-on "HTML Editor Tweaks" is used.
- `"font-family"` (default is `"monospace"`), `"font-size"` (default is `"15px"`): font and font size used in the editor window for the html source code.
- `backup_template_path` (default "false"): If false the versions are saved to a subfolder in the add-on folder in your anki profile.
- `external: show this option in clayout context`: That's off by default since I don't have a Mac and could never test this on MacOS and expect that there are problems with the MacOS permission system. On Windows and Linux it mostly worked in 2020 but I didn't test this functionality later. If you are interested in this functionality in 2022 the best maintained add-on seems to be [External Note Editor (vim, vscode, atom, ...)](https://ankiweb.net/shared/info/704320065).
- `editor_diff` (default `"code --diff"`): Must be a string. This is the command to compare versions. The add-on extends this with two filenames and then this command is called.
- `anki editor: add button`: whether a button on the top right of the editor should be shown. If you also use the add-on "Customize Keyboard Shortcuts" keep this value "true" - otherwise hotkey_codemirror won't work. Maybe there are also conflicts with other add-ons.
- `hotkey_codemirror` (default "Ctrl+Shift+Y"): shortcut to open the html source view window
- `keymap`: For details see the official documentation [here](https://codemirror.net/doc/manual.html#keymaps). Other values are "emacs" or "vim". Changes take only effect after restarting Anki.
- `theme` and `theme night mode`: For a list of available themes see [here](https://codemirror.net/demo/theme.html). Changes take only effect after restarting Anki.

&nbsp;

For Windows users: When adjusting `"external: command to open field content in editor"` or `editor_diff` remember to escape (duplicate) the backslashes in a path (json uses backslash as a special character), e.g.

    {
        "external: command to open field content in editor": "c:\\Program Files\\Notepad++\\notepad++.exe"
    }


#### some useful keycombos for the default keymap

- "Esc": Close window, discard changes
- "Ctrl+F": Find
- "Ctrl-H": Replace
- "Ctrl-Alt-Up": addCursorToPrevLine
- "Ctrl-Alt-Down": addCursorToNextLine
- "Ctrl-F3": search for word under cursor (findUnderNext)
- "Shift-Ctrl-F3": search for word under cursor backwards (findUnderPrevious)
