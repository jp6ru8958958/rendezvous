# rendezvous
### Python - Built-in `venv`

Create your virtual environment:

    python3 -m venv venv
    . venv/bin/activate
	export PATH=“$HOME/.pyenv/bin:$PATH”

Use pip to install Python depedencies:

    pip install -r requirements.txt

Copy the settings.py and add sensitive informations. `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`, [Django secret key](https://miniwebtool.com/django-secret-key-generator/)

	cp rendezvous/settings_copy.py rendezvous/settings.py
