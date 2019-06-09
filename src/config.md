- `hotkey_codemirror` (default "Ctrl+Shift+Y"): shortcut to open the html source view window
- `default_height`, `default_width`: initial size for the html source view window
- `format` (default "bs4-prettified"): If you want to get formatting as in the add-on "HTML Editor Tweaks" use "tweaked", to get the html formatted by pretty function of the python module beautifulsoup use "bs4-prettified" and None if the html should be unmodified. 
- `theme`: For a list of available themes see [here](https://codemirror.net/demo/theme.html). Changes take only effect after restarting Anki.
- `keymap`: For details see the official documentation [here](https://codemirror.net/doc/manual.html#keymaps). Other values are "emacs" or "vim". Changes take only effect after restarting Anki.

<b>some useful keycombos</b>:

- "Esc": Close window, discard changes
- "Ctrl+F": Find
- "Ctrl-H": Replace
- "Ctrl-Alt-Up": addCursorToPrevLine
- "Ctrl-Alt-Down": addCursorToNextLine
- "Ctrl-F3": search for word under cursor (findUnderNext)
- "Shift-Ctrl-F3": search for word under cursor backwards (findUnderPrevious)
