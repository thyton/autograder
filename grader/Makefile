VENV = . env/bin/activate;

all: image service production

devenv:
	kubectl run grader -it --rm --image=python:3.7.0 --restart=Never --overrides="$$(cat development.json)"

TAG=grader:v1
DEPLOYMENT=grader
-include ../docker.Makefile
-include ../k8s.Makefile



run: env
	$(VENV) python main.py

test: env
	$(VENV) python tests.py

env: requirements.txt
	test -d env || python3 -m venv env --copies
	$(VENV) pip install -r requirements.txt
	touch env

freeze:
	$(VENV) pip freeze > requirements.txt

clean:
	$(RM) data.db
	$(RM) -r __pycache__
clean-env:
	$(RM) -r env

.PHONY: run dev test env db freeze

