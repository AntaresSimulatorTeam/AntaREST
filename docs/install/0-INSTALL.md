# Introduction

Antares Web is developed mainly in **Python** and uses [FastAPI](https://fastapi.tiangolo.com/) web framework.
The front end is a [React](https://reactjs.org/) web application.
A local build allows using Antares Web as a desktop application.

## Quick start

Requirements:

- python : 3.8.x
- node : 18.16.1

Then perform the following steps:

1. First clone the projet:

   ```shell
   git clone https://github.com/AntaresSimulatorTeam/AntaREST.git
   cd AntaREST
   ```

2. Create and activate a Python virtual environment:

   ```shell
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies to build, test or develop the back end:

   ```shell
   python3 -m pip install --upgrade pip
   pip install -e .                     # to install in development mode (editable)
   pip install -r requirements-dev.txt  # production, unit tests and development requirements
   ```

4. Install dependencies to build the front end:

   ```shell
   cd webapp
   npm install
   npm run build
   cd ..
   ```

   > IMPORTANT : make sur the generated files are in the `dist` (or `build`) folder.
   > Using another folder may require substantial adaptations in the CI/CD pipelines.

5. Run the application

   ```shell
   python3 antarest/main.py -c resources/application.yaml --auto-upgrade-db --no-front
   ```

## Deploy

There are 2 ways to use and/or deploy the application:

- As [a server application](./2-DEPLOY.md#production-server-deployment)
- As [a desktop systray application](./2-DEPLOY.md#local-application-build)