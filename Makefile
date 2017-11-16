nothing:
	@echo "nothing do do here"

pex:
	mkdir -p pex
	virtualenv venv-pex
	. venv-pex/bin/activate && pip install pex && pex . -r requirements.txt -m idbiaas.idbiaas -o pex/idbiaas.pex && deactivate
	rm -rf venv-pex

