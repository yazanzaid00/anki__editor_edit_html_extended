function findHiddenCharacters(node, beforeCaretIndex) {
    var hiddenCharacters = 0
    var lastCharWasWhiteSpace=true
    for(var n=0; n-hiddenCharacters<beforeCaretIndex &&n<node.length; n++) {
        if([' ','\\n','\\t','\\r'].indexOf(node.textContent[n]) !== -1) {
            if(lastCharWasWhiteSpace)
                hiddenCharacters++
            else
                lastCharWasWhiteSpace = true
        } else {
            lastCharWasWhiteSpace = false   
        }
    }

    return hiddenCharacters
}

var setSelectionByCharacterOffsets = null;

if (window.getSelection && document.createRange) {
    setSelectionByCharacterOffsets = function(containerEl, position) {
        var charIndex = 0, range = document.createRange();
        range.setStart(containerEl, 0);
        range.collapse(true);
        var nodeStack = [containerEl], node, foundStart = false, stop = false;

        while (!stop && (node = nodeStack.pop())) {
            if (node.nodeType == 3) {
                var hiddenCharacters = findHiddenCharacters(node, node.length)
                var nextCharIndex = charIndex + node.length - hiddenCharacters;

                if (position >= charIndex && position <= nextCharIndex) {
                    var nodeIndex = position - charIndex
                    var hiddenCharactersBeforeStart = findHiddenCharacters(node, nodeIndex)
                    range.setStart(node, nodeIndex + hiddenCharactersBeforeStart );
                    range.setEnd(node, nodeIndex + hiddenCharactersBeforeStart);
                    stop = true;
                }
                charIndex = nextCharIndex;
            } else {
                var i = node.childNodes.length;
                while (i--) {
                    nodeStack.push(node.childNodes[i]);
                }
            }
        }

        var sel = window.getSelection();
        sel.removeAllRanges();
        sel.addRange(range);
    }
} else if (document.selection) {
    setSelectionByCharacterOffsets = function(containerEl, start, end) {
        var textRange = document.body.createTextRange();
        textRange.moveToElementText(containerEl);
        textRange.collapse(true);
        textRange.moveEnd("character", end);
        textRange.moveStart("character", start);
        textRange.select();
    };
}


setSelectionByCharacterOffsets(currentField, %s)