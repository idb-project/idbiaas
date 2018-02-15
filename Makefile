_NAME := idbiaas
_DISTNAME := bytemine-idbiaas

distfile: pex/idbiaas.pex
	mkdir -p /tmp/$(_DISTNAME)-$(VERSION)
	cp pex/$(_NAME).pex /tmp/$(_DISTNAME)-$(VERSION)
	cd /tmp && tar cvzf $(_DISTNAME)-$(VERSION).tgz $(_DISTNAME)-$(VERSION)
	sha256sum /tmp/$(_DISTNAME)-$(VERSION).tgz

pex/idbiaas.pex: requirements.txt idbiaas/idbiaas.py setup.py venv-pex
	mkdir -p pex
	. venv-pex/bin/activate && pex . --disable-cache -r requirements.txt -m idbiaas.idbiaas -o pex/idbiaas.pex && deactivate

venv-pex:
	virtualenv venv-pex
	. venv-pex/bin/activate && pip install pex

clean:
	rm -rf pex
	rm -rf venv-pex

