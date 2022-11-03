# About

Fever Dreams backend API

## Installation (Linux/Macos)

```sh
python3 -m pip install --user virtualenv
python -m venv .venv/fd-api
source .venv/fd-api/bin/activate
pip install -r requirements.txt
```

## Installation (Windows)

```ps
python3 -m pip install --user virtualenv
python -m venv .venv/fd-api
.venv\fd-api\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Initial Configuration

- Adjust `config/default.py` to match your environment configuration.
- Create `instance/config.py` to store your secrets/tokens/credentials.  Refer to `exampleconfig.py` for details.

## Run/Debug Locally

```sh
flask --debug --app api.py run
```

## Run in a Deployment

```sh
gunicorn -b 0.0.0.0:8080 --workers=15 --threads 2 --backlog 2048 --worker-connections 1000 api:app
```