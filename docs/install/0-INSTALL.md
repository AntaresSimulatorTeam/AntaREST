# Introduction

Antares-Web is developed mainly in **python** and uses [FastAPI](https://fastapi.tiangolo.com/) web framework.
The front end is a [React](https://reactjs.org/) web application. A local build allows using Antares-Web as a desktop application.

## Build and installation details

First clone the projet:

```shell script
git clone https://github.com/AntaresSimulatorTeam/AntaREST.git
cd AntaREST
git submodule init
git submodule update
```

Install back dependencies

```shell script
python -m pip install --upgrade pip
pip install pydantic --no-binary pydantic
pip install -r requirements.txt  # use requirements-dev.txt if building a single binary with pyinstaller 
```

Build front

```shell script
cd webapp
npm install
cd ..
NODE_OPTIONS="--max-old-space-size=8192" ./scripts/build-front.sh
```

