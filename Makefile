SHELL=/bin/bash

PYTHON=${VENV_BIN}/python3

build:
	rm illumidesk.zip || true
	find ./src/ -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete -o -type f -name .DS_Store -delete
	zip -r compose/jupyterhub/illumidesk.zip src/
	docker build -t illumidesk/jupyterhub:k8s-beta -f compose/jupyterhub/Dockerfile.jhub ./compose/jupyterhub

push:
	docker login
	docker push illumidesk/jupyterhub:k8s-beta
