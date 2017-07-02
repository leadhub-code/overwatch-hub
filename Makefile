python3=python3
venv_dir=local/venv
conf_path=sample-configuration.yaml

run: $(venv_dir)/packages-installed
	env \
		OVERWATCH_HUB_CONF=$(conf_path) \
		PYTHONDONTWRITEBYTECODE=1 \
		FLASK_APP=overwatch_hub:app \
		FLASK_DEBUG=1 \
		$(venv_dir)/bin/flask run --host=0.0.0.0

run-mongo:
	mkdir -p local/mongo-data
	mongod -dbpath local/mongo-data -bind_ip 127.0.0.1 -port 27017

$(venv_dir)/packages-installed: setup.py
	test -d $(venv_dir) || $(python3) -m venv $(venv_dir)
	$(venv_dir)/bin/pip install pip wheel
	$(venv_dir)/bin/pip install -e .
	touch $@
