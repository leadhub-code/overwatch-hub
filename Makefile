python3=python3
venv_dir=local/venv

run: $(venv_dir)/packages-installed
	env \
		PYTHONDONTWRITEBYTECODE=1 \
		FLASK_APP=overwatch_hub:app \
		FLASK_DEBUG=1 \
		$(venv_dir)/bin/flask run

$(venv_dir)/packages-installed: setup.py
	test -d $(venv_dir) || $(python3) -m venv $(venv_dir)
	$(venv_dir)/bin/pip install pip wheel
	$(venv_dir)/bin/pip install -e .
	touch $@
