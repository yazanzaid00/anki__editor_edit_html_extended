// selection_utils.js (modified)

window.ankiGetSelectionData = function () {
  // … your existing selection + HTML-cleanup logic up to final_html …
  let sel = (document.activeElement?.shadowRoot
    ? document.activeElement.shadowRoot.getSelection()
    : (document.activeElement?.getSelection
      ? document.activeElement.getSelection()
      : window.getSelection()));
  if (!sel || !sel.rangeCount) { return { html: "", text: "" }; }

  const c = document.createElement("div");
  c.append(sel.getRangeAt(0).cloneContents());

  // Store HTML before modification for plain text
  const html_content = c.innerHTML;

  c.querySelectorAll('anki-frame,frame-start,frame-end')
    .forEach(n => n.replaceWith(...n.childNodes));
  c.querySelectorAll('[data-frames]').forEach(n => n.removeAttribute('data-frames'));

  c.querySelectorAll('anki-mathjax').forEach(el => {
    let tex = el.getAttribute('data-mathjax');
    if (!tex && window.MathJax?.Hub?.getJaxFor) {
      const jax = MathJax.Hub.getJaxFor(el);
      tex = jax?.originalText;
    }
    tex = tex || el.textContent;
    const clean = document.createElement('anki-mathjax');
    clean.textContent = tex;
    el.replaceWith(clean); // For HTML output
  });

  const final_html = c.innerHTML; // HTML after anki-mathjax processing


  // ——————————————————————————
  // Helper: skip over whitespace-only text nodes
  function siblingHasBreak(el, dir) {
    let n = dir === 'prev' ? el.previousSibling : el.nextSibling;
    while (n) {
      if (n.nodeType === Node.ELEMENT_NODE) {
        return n.tagName === 'BR';
      }
      if (n.nodeType === Node.TEXT_NODE) {
        if (n.textContent.includes('\n')) {
          return true;
        }
        if (n.textContent.trim() === '') {
          n = dir === 'prev' ? n.previousSibling : n.nextSibling;
          continue;
        }
        return false;
      }
      break;
    }
    return false;
  }

  // Decide display vs inline
  function isDisplayContext(node) {
    const el = node.nodeType === Node.ELEMENT_NODE
      ? node
      : node.parentElement;
    if (!el || !el.parentElement) {
      return false;
    }

    // Case 1: formula is the **only** real content of a DIV
    const p = el.parentElement;

    /* ─── Case 0 : selection contains only the formula (no other real
       content at top level) ───────────────────────────────────────── */
    if (p === ROOT) {
      const onlyWS = n => n.nodeType === 3 && n.textContent.trim() === '';
      if ([...ROOT.childNodes].filter(n => n !== el && !onlyWS(n)).length === 0) {
        return true;
      }
    }

    if (p !== ROOT && p.tagName === 'DIV') {
      const onlyWhitespace = n =>
        n.nodeType === Node.TEXT_NODE && n.textContent.trim() === '';
      const others = [...p.childNodes].filter(n => n !== el && !onlyWhitespace(n));
      if (others.length === 0) {
        return true;
      }
    }

    // Case 2 & 3: <br> before or after?
    const before = siblingHasBreak(el, 'prev');
    const after = siblingHasBreak(el, 'next');
    if (before || after) {
      return true;
    }

    return false;
  }

  // rebuild text-only DOM and wrap with \[…\] or \(...\)
  const text_c = document.createElement("div");
  text_c.innerHTML = html_content; // original un-modified HTML
  const ROOT = text_c;             // remember our synthetic wrapper

  // ─── new: strip out Anki’s frame markers here too ───
  text_c.querySelectorAll('anki-frame,frame-start,frame-end')
    .forEach(n => n.replaceWith(...n.childNodes));
  text_c.querySelectorAll('[data-frames]').forEach(n => n.removeAttribute('data-frames'));
  // ────────────────────────────────────────────────────

  text_c.querySelectorAll('anki-mathjax').forEach(el => {
    const tex = el.getAttribute('data-mathjax') || el.textContent;
    const wrapped = isDisplayContext(el)
      ? '\\[' + tex + '\\]'
      : '\\(' + tex + '\\)';
    el.replaceWith(document.createTextNode(wrapped));
  });

  // final clean-up: remove stray hair-spaces etc. and tidy up newlines
  let txt = text_c.innerText;
  // replace non-breaking & hair-spaces with normal space
  txt = txt.replace(/[\u00A0\u200A\u2009\u200B]/g, ' ');
  // trim spaces at EOL or BOL
  txt = txt.replace(/[ \t]+\n/g, '\n')
    .replace(/\n\s+/g, '\n');
  return {
    html: final_html,
    text: txt.trim()
  };
};
