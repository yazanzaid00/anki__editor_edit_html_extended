import bs4
import re

from .config import gc
from .htmlmin import Minifier


open_space_open = re.compile('(<[^/>]+>) (<[^/>]+>)')
close_space_close = re.compile('(</[^>]+>) (</)')
open_space_text = re.compile('(<[^/>]+>) ([^<>]+)')
open_text_close = re.compile('(<[^/>]+>) ([^<>]+) (</)')
tag_space_punc = re.compile('(>) ([.,:;])')


# the function postprocess from https://ankiweb.net/shared/info/410936778 
# doesn't work with syntax highlighted code


def maybe_minify(s):
    if not gc("Format code after closing (minify/compact)", True):
        return s
    minifier = Minifier()
    # "splitlines" breaks "pre"!
    #     https://developer.mozilla.org/en-US/docs/Web/HTML/Element/pre
    #     The HTML <pre> element represents preformatted text which is to be presented exactly as 
    #     written in the #HTML file. The text is typically rendered using a non-proportional 
    #     ("monospace") font. Whitespace inside this element is displayed as written.
    #for l in s.splitlines():
    #    minifier.input(l)
    #out = minifier.output
    minifier.input(s)
    out = minifier.output
    return out


def reindent(s, factor=4):
    """Increase indentation of pretty printed HTML.

    Beautiful Soup indents by a single space at each indentation level,
    probably because it also places each tag on its own line, resulting
    in heavily nested markup. In many situations this will pose
    readability issues, but in Anki the editor only deals with HTML
    fragments, not entire documents. 4 spaces is more reasonable.
    """
    t = []
    for line in s.split('\n'):
        r = re.match('( +)([^ ].*)', line)
        if r:
            n = len(r.group(1)) * factor
            t.append('{}{}'.format(' ' * n, r.group(2)))
        else:
            t.append(line)
    return '\n'.join(t)


def maybe_format__prettify(html):
    if gc("Format code before opening (unfold)") not in ["bs4-prettified", "tweaked"]:
        return html
    bs4ed = bs4.BeautifulSoup(html, "html.parser").prettify(formatter='html5')
    if gc("Format code before opening (unfold)") == "bs4-prettified":    
        return bs4ed
    else: # gc("Format code before opening (unfold)") == "tweaked":
        return reindent(bs4ed)
