# Antares Web

[![CI](https://github.com/AntaresSimulatorTeam/AntaREST/workflows/main/badge.svg)](https://github.com/AntaresSimulatorTeam/AntaREST/actions?query=workflow%3Amain)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=AntaresSimulatorTeam_api-iso-antares&metric=coverage)](https://sonarcloud.io/dashboard?id=AntaresSimulatorTeam_api-iso-antares)
[![Licence](https://img.shields.io/github/license/AntaresSimulatorTeam/AntaREST)](https://www.apache.org/licenses/LICENSE-2.0)

![Screenshot](./docs/assets/media/img/readme_screenshot.png)

## Documentation

The full project documentation can be found in the [readthedocs website](https://antares-web.readthedocs.io/en/latest).

## Build the API

First clone the projet:

```shell script
git clone https://github.com/AntaresSimulatorTeam/AntaREST.git
cd AntaREST
```

Install back-end dependencies

```shell script
python -m pip install --upgrade pip
pip install -r requirements.txt  # use requirements-dev.txt if building a single binary with pyinstaller 
```

Install the front-end dependencies:

```shell script
cd webapp
npm install
cd ..
```

Then build the front-end application:
 - for use with pyinstaller:
```shell
NODE_OPTIONS="--max-old-space-size=8192" ./scripts/build-front.sh
```
 - for other uses (docker deployement, ...):
```shell
cd webapp
npm run build
cd ..
```


### Using pyinstaller

Linux system:

```shell script
git log -1 HEAD --format=%H > ./resources/commit_id
pyinstaller AntaresWebLinux.spec
```

Windows system:

```shell script
git log -1 HEAD --format=%H > .\resources\commit_id
pyinstaller AntaresWebWin.spec
```

You can test the build is ok using:

```shell script
dist/AntaresWeb/AntaresWebServer -v       # Linux based system
dist\AntaresWeb\AntaresWebServer.exe -v   # Windows system
```

### Using docker

To build the docker image, use the following command:

```shell script
docker build --tag antarest .
```

## Run the API

### Using binary built with pyinstaller

```shell script
dist/AntaresWeb/AntaresWebServer -c </path/to/config.yaml>  # Linux based system
dist\AntaresWeb\AntaresWebServer.exe -c </path/to/config.yaml>    # Windows system
```

### Using docker image

You may run the back-end with default configuration using the following command:
```shell script
docker run \
  -p 80:5000 \
  -e GUNICORN_WORKERS=1 \
  antarest
```

However, for a complete deployment including the front-end application, and the use of an external database
and an external REDIS instance, please refer to the deployement instructions on [readthedocs website](https://antares-web.readthedocs.io/en/latest)


### Using python directly

#### Using uvicorn

```shell script
pip install -e .

python ./antarest/main.py -c resources/application.yaml
```

#### Using gunicorn wsgi server with uvicorn workers

```shell script
pip install -e .

export ANTAREST_CONF=resources/application.yaml
export GUNICORN_WORKERS=4
gunicorn --config conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app
```

## Examples

Once you started the server, you have access to the API.
The address (the port mostly) depends of the way you started the server. If you start the server
* via python use: **http://0.0.0.0:8080**
* via gunicorn use: **http://0.0.0.0:5000**
* via docker use: **http://0.0.0.0:80** (if you use the parameter *-p 80:5000*)

To test the server, you can list the available studies in your workspace using:

```shell script
curl http://localhost:8080/v1/studies
```

Or data of a specific study using:

```shell script
curl http://localhost:8080/v1/studies/{study_uuid}
```

The current API handle hundreds of html end point (get and post) to manipulate your studies.
The best way to discover the API is using it's swagger documentation (see below).

## Swagger

The ANTARES API doc is available within the application (open your browser to `http://localhost:8080`)
You can also fetch the raw open api spec :

```shell script
curl http://localhost:8080/openapi.json > swagger.json
```