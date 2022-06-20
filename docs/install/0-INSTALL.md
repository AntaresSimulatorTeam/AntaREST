# Introduction

Antares-Web is developed mainly in **python** and uses [FastAPI](https://fastapi.tiangolo.com/) web framework.
The front end is a [React](https://reactjs.org/) web application. A local build allows using Antares-Web as a desktop application.

## Quick start

Requirements : 
- python : 3.8.x
- node : 14.x

1. First clone the projet:

```
git clone https://github.com/AntaresSimulatorTeam/AntaREST.git
cd AntaREST
git submodule init
git submodule update
```

2. Install back dependencies

```
python -m pip install --upgrade pip
pip install pydantic --no-binary pydantic
pip install -r requirements.txt  # use requirements-dev.txt if building a single binary with pyinstaller 
```

3. Build front (for local mode use `cd ..; ./scripts/build-front.sh` instead of `npm run build`)

```
cd webapp
npm install
npm run build 
```

4. Run the application

```
export PYTHONPATH=$(pwd)
python antarest/main.py -c resources/application.yaml --auto-upgrade-db
```

## Deploy

There is to way to use and/or deploy the application :
- As [a server application](./2-DEPLOY.md#production-server-deployment)
- As [a desktop systray application](./2-DEPLOY.md#local-application-build)