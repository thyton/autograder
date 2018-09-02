service:
	kubectl create -f service.yaml || true

development:
	kubectl create -f development.yaml

production:
	kubectl create -f production.yaml || true

update-image:
	kubectl set image deployment/$(DEPLOYMENT) $(DEPLOYMENT)=$(TAG)


