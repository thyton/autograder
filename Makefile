help:
	@echo 'before running, you must ensure that Docker and kubectl are configured'
	@echo 'if you are using Minikube, you must run the `minikube start` and `eval $$(minikube docker-env)` commands yourself'
	@echo 'afterwards, run `make devenv`'

devenv: services mounts running

running:
	@echo 'the infrastructure services are running'
	@echo 'you must manually run the frontend and backend services'
	@echo 'to do so, open a new terminal for each service (frontend, grader, deplagiarizer),'
	@echo 'cd into the corresponding folder and run `make devenv`'
	@echo 'if you are not actively working on a service, you can just make the service'
	@echo '(eg `make frontend`) to create and run a service image'

services: mq
	cd frontend && $(MAKE) service

mounts: frontend-mount grader-mount deplagiarizer-mount

frontend-mount:
	minikube mount $(PWD)/frontend:/src/frontend &

grader-mount:
	minikube mount $(PWD)/grader:/src/grader &

deplagiarizer-mount:
	minikube mount $(PWD)/deplagiarizer:/src/deplagiarizer &

production: frontend gateway mq grader

gateway:
	cd gateway && $(MAKE)

mq:
	cd mq && $(MAKE)

grader:
	cd grader && $(MAKE)

frontend:
	cd frontend && $(MAKE)

deplagiarizer:
	cd deplagiarizer && $(MAKE)


de-taint:
	kubectl taint nodes --all node-role.kubernetes.io/master-

.PHONY: gateway mq frontend grader deplagiarizer

