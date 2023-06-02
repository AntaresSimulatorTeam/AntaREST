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

Install backend dependencies

```shell script
python -m pip install --upgrade pip
pip install pydantic --no-binary pydantic
pip install -r requirements.txt  # use requirements-dev.txt if building a single binary with pyinstaller 
```

Build frontend

```shell script
cd webapp
npm install
cd ..
NODE_OPTIONS="--max-old-space-size=8192" ./scripts/build-front.sh
```


### Using pyinstaller

Linux system:

```shell script
git log -1 HEAD --format=%H > ./resources/commit_id
pyinstaller -F antarest/main.py -n server --additional-hooks-dir extra-hooks --add-data resources:resources
```

Windows system:

```shell script
git log -1 HEAD --format=%H > .\resources\commit_id
pyinstaller -F api_iso_antares\main.py -n server --additional-hooks-dir extra-hooks --add-data ".\resources;.\resources"
```

You can test the build is ok using:

```shell script
dist/server -v       # Linux based system
dist\server.exe -v   # Windows system
```

### Using docker

To build the docker image, use the following command:

```shell script
docker build --tag antarest .
```

## Run the API

### Using binary built with pyinstaller

```shell script
dist/server -s $STUDIES_ABSOLUTE_PATH         # Linux based system
dist\server.exe -s %STUDIES_ABSOLUTE_PATH%    # Windows system
```

* $STUDIES_ABSOLUTE_PATH is the path of the ANTARES studies folders you wish to manipulate

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

#### Using the dev wsgi server of Flask

```shell script
pip install -r ./requirements.txt
export PYTHONPATH=$PYTHONPATH:.
python ./api_iso_antares/main.py -s $STUDIES_ABSOLUTE_PATH
```

* $STUDIES_ABSOLUTE_PATH is the path of the ANTARES studies folders you wish to manipulate
* An exemple is available in this repo in the *script* folder

#### Using gunicorn wsgi server

```shell script
pip install -r ./requirements.txt
export PYTHONPATH=$PYTHONPATH:.

export ANTAREST_CONF=$ANTAREST_CONF_YAML_PATH
export GUNICORN_WORKERS=4

gunicorn --config "$YOUR_GUNICORN_CONFIG" antarest.wsgi:app
```

* $YOUR_GUNICORN_CONFIG is the path of a gunicorn server configuration file
    * An example is available in this repo in the *conf* folder
* Setting the environment variable GUNICORN_WORKERS to *ALL_AVAILABLE* will make GUNICORN use 2 * nb_cpu +1 workers
    * https://docs.gunicorn.org/en/stable/design.html#how-many-workers
    * ALL_AVAILABLE is also the default value of GUNICORN_WORKERS if you do not set it
* An exemple is available in this repo in the *script* folder

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