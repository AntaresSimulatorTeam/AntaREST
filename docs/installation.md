# Build from source

A local build allows using Antares Web as a desktop application.

## Quick start

Requirements:

- python : 3.11.x
- node : 22.13.0
- uv : latest (see [installation](https://docs.astral.sh/uv/getting-started/installation/))

Then perform the following steps:

1. First clone the projet:

   ```shell
   git clone https://github.com/AntaresSimulatorTeam/AntaREST.git
   cd AntaREST
   ```

2. Install back-end dependencies using uv:

   ```shell
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install all dependencies (production, test, and dev)
   uv sync --all-extras
   ```

3. Install dependencies to build the front end:

   ```shell
   cd webapp
   npm install
   npm run build
   cd ..
   ```

   > IMPORTANT : make sur the generated files are in the `dist` (or `build`) folder.
   > Using another folder may require substantial adaptations in the CI/CD pipelines.

4. Run the application

   ```shell
   uv run python antarest/main.py -c resources/application.yaml --auto-upgrade-db --no-front
   ```
