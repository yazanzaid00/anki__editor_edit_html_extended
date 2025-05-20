PACKAGE_NAME = 1900436383.ankiaddon

package zip:
	zip -r $(PACKAGE_NAME) . -x "__pycache__/*" -x "*.py[cod]"

run:
	@if pgrep -f "/Applications/Anki.app" > /dev/null; then \
		echo "Error: Anki.app is already running. Please close it and try again."; \
		exit 1; \
	fi
	rm -f anki_output.log && printf '\033c\x1b[3J\x1b[H\x1b[2J' && /Applications/Anki.app/Contents/MacOS/Anki > anki_output.log 2>&1

.PHONY: package run
