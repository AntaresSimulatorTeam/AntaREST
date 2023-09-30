# Application Configuration

Almost all the configuration of the application can be found in the 
[application.yaml](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/resources/application.yaml) file.
If the path to this configuration file is not explicitly provided (through the `-c` option),
the application will try to look for files in the following location (in order):

 1. `./config.yaml`
 2. `../config.yaml`
 3. `$HOME/.antares/config.yaml`

