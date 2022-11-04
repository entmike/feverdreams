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

- Adjust environment variables used in `config/default.py`
- Adjust environment variables used in `instance/config.py`

## Run/Debug Locally

```sh
flask --debug --app api.py run
```

## Run in a Deployment

```sh
gunicorn -b 0.0.0.0:8080 --workers=15 --threads 2 --backlog 2048 --worker-connections 1000 api:app
```

## Run in Docker
```sh
docker run -it --rm -p 8080:8080 \
    -e BOT_SALT="SaltPhrase" \
    -e BOT_AWS_SERVER_PUBLIC_KEY="YOURAMAZONPUBLICKEY" \
    -e BOT_AWS_SERVER_SECRET_KEY="YourAmazonSecretKey" \
    -e AUTH0_MGMT_API_CLIENT_ID="YourAuth0ClientId" \
    -e AUTH0_MGMT_API_SECRET="YourAuto0Secret" \
    -e MONGODB_CONNECTION="mongodb://yourmongohost:27017" \
    entmike/fdapi bash -c "gunicorn -b 0.0.0.0:8080 --workers=15 --threads 2 --backlog 2048 --worker-connections 1000 api:app"
```