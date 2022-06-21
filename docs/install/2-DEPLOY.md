# Deployments

This application can be used in two modes:
- a production dockerized environment
- a local desktop application

## Production server deployment

The production server deployment uses `docker` and `docker-compose` to run the following containers :
- antarest : the web application workers
- antarest-watcher : the workspace scanner worker
- antarest-matrix-gc: the matrices garbage collector worker 
- redis : the cache that allows the multiple application server workers to synchronize
- postgresql : the database
- nginx : the web server front end (can be used to set up ssl)

The following example shows how to deploy this simple base environment.

### Example deployment steps

Requirements :
- a linux host
- docker
- docker-compose

These steps should work on any linux system with docker and docker-compose installed.

0. First, the steps 1 and 3 of the [quick start build](0-INSTALL.md#quick-start) must have been done. So this guide will assume that you have previously cloned the [code repository](https://github.com/AntaresSimulatorTeam/AntaREST)
   (don't forget the git submodule), the frontend built and that your working directory is at the root of the project.

1. Then download and unzip AntaresSimulator binaries:
```
wget https://github.com/AntaresSimulatorTeam/Antares_Simulator/releases/download/v8.2.2/antares-8.2.2-Ubuntu-20.04.tar.gz
tar xzf antares-8.2.2-Ubuntu-20.04.tar.gz
```

2. Build the docker image
```
docker build -t antarest:latest .
```

3. Prepare the environment (This is important, in order to prevent docker containers to write files into your file system with root permissions.)  
   a. Copy `docker-compose.override.yml.example` to `docker-compose.override.yml` and replace the UID and GUI values with your user's one.  
You can get these values by running the following commands:
   - UID: `id -u`
   - GID: `id -g`

   b. Create the directory `resources/deploy/db`
    

4. Run the following command to spin up the application containers :  
`docker-compose up`
   
5. You can then access the application at http://localhost

6. To stop the application you can juste hit "CTRL-C" to end the containers

This is an example deployment.  
You'll have to edit your own `docker-compose.yml` file and [`application.yaml` configuration](./1-CONFIG.md) to customize it to your needs.

## Local application build

The local application is a bundled build of the web server to ease its launch as a kind of desktop application.  
When started, the application will be shown as a systray application (icon in the bottom right corner of the Windows bar). The menu will allow to go
to the local address where the interface is available.

The build is directly available in the [release](https://github.com/AntaresSimulatorTeam/AntaREST/releases) files for each version.
You can download the latest version here :
- [For Windows](https://github.com/AntaresSimulatorTeam/AntaREST/releases/download/v2.5.0/AntaresWeb-windows-latest.zip)
- [For Ubuntu](https://github.com/AntaresSimulatorTeam/AntaREST/releases/download/v2.5.0/AntaresWeb-ubuntu-latest.zip)
