# Application Configuration Documentation

Almost all the configuration of the application can be found in the 
[application.yaml](https://github.com/AntaresSimulatorTeam/AntaREST/blob/master/resources/application.yaml) file.
If the path to this configuration file is not explicitly provided (through the `-c` option),
the application will try to look for files in the following location (in order):

 1. `./config.yaml`
 2. `../config.yaml`
 3. `$HOME/.antares/config.yaml`

# File Structure
- [Security](#security) 
- [Database](#database)
- [Storage](#storage)
- [Launcher](#launcher)
- [Logging](#logging)
- [Root Path](#root_path)
- [Optional sections](#debug)

# security
This section concerns application security, authentication and groups
## **disabled**
  - **Type:** Boolean
  - **Default value:** False
  - **Description:** If value is `False`, user identification is required when launching the app
## **jwt**
### **key**
- **Type:** String
- **Default value:** Empty String
- **Description:** JWT(Json Web Token) secret key for authentication
## **login**
### **admin**
#### **pwd**
- **Type:** String
- **Default value:** Empty String
- **Description:** Admin user's password
## **external_auth**
### **url**
- **Type:** String
- **Default value:** None
- **Description:** External authentication URL. If you want to enable local authentication, you should write an Empty String. To enable authentication via RTE "NNI", you should register http://antarestgaia:8080
### **default_group_role**
- **Type:** Integer, possible values: 10, 20, 30, 40
- **Default value:** 10
- **Description:** Default user role for external authentication. ADMIN = 40, WRITER = 30, RUNNER = 20, READER = 10
### **add_ext_groups**
- **Type:** Boolean
- **Default value:** False
- **Description:** Whether to add external groups to user roles
### **group_mapping**
- **Type:** Dictionary
- **Default value:** Empty Dictionary
- **Description:** Groups of the application: Keys = Ids, Values = Names. Example:
  - 00000001: espace_commun
  - 00001188: drd
  - 00001574: cnes


# database
This section concerns application's database information
## **url**
- **Type:** String
- **Default value:** Empty String
- **Description:** Database URL. Example: `sqlite:///database.db`for a local SQLite DB or `postgresql://postgres_user:postgres_password@postgres_host:postgres_port/postgres_db` for a PostgreSQL DB.
## **admin_url**
- **Type:** String
- **Default value:** None
- **Description:** The URL you can use to directly access your database.
## **pool_use_null**
- **Type:** Boolean
- **Default value:** False
- **Description:** If `True`, the Pool does not pool connections. This parameter should stay at `False` to avoid issues.
## **db_connect_timeout**
- **Type:** Integer
- **Default value:** 10
- **Description:** Database timeout (in seconds) to create the connection
## **pool_recycle**
- **Type:** Integer
- **Default value:** None
- **Description:** Prevents the pool from using a particular connection that has passed a certain time in seconds. An often used value is 3600 which corresponds to a day. *Not used for SQLite DB*
## **pool_size**
- **Type:** Integer
- **Default value:** 5
- **Description:** Maximum number of permanent connections to keep. *Not used for SQLite DB*
## **pool_use_lifo**
- **Type:** Boolean
- **Default value:** False
- **Description:** Should Database use Last-in First-out method. It is commonly used in cases where the most recent data entry is the most important and that applies to the application context. Therefore, it's better to set this parameter to `True`. *Not used for SQLite DB*
## **pool_pre_ping**
- **Type:** Boolean
- **Default value:** False
- **Description:** Connections which are closed from the server side are gracefully handled by the connection pool and replaced with a new connection. *Not used for SQLite DB*
## **pool_max_overflow**
- **Type:** Integer
- **Default value:** 10
- **Description:** Temporarily exceeds the set pool_size if no connections are available. *Not used for SQLite DB*


# storage
This section concerns application Paths and Services options
## **tmp_dir**
- **Type:** Path
- **Default value:** tempfile.gettempdir() (doc here: [tempfile_doc](https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir))
- **Description:** Temporary directory for storing temporary files. Often used value : `./tmp`
## **matrixstore**
- **Type:** Path
- **Default value:** `./matrixstore`
- **Description:** Antares Web extract matrices data and share them between managed studies to save space. These matrices are stored here. 
## **archive_dir**
- **Type:** Path
- **Default value:** `./archives`
- **Description:** Directory for archived (which means zipped) studies
## **workspaces**
- **Type:** Dictionary
- **Default value:** Empty Dictionary
- **Description:** Different workspaces where the application expects to find studies.
Keys = Folder names, Values = WorkspaceConfig object. Such an object has 4 fields:
  - groups: List of groups corresponding to the workspace (default Empty List)
  - path: Path of the workspace (default Path())
  - filter_in: List of regex. If a folder does not contain a file whose name matches one of the regex , it's not scanned (default [".*"])
  - filter_out: List of regex. If a folder contains any file whose name matches one of the regex, it's not scanned (default Empty List)
  
*NB: If a directory is to be ignored by the watcher, place a file named AW_NO_SCAN inside*

Examples:
```
    default:
      path: /home/john/Projects/antarest_data/internal_studies/  
    studies:
      path: /home/john/Projects/antarest_data/studies/  
    staging_studies:
      path: /home/john/Projects/antarest_data/staging_studies/  
```
```
default:
  path: /studies/internal
"public":
  path: /mounts/public
    filter_in: 
      - .*
    filter_out: 
      - ^R$
      - System Volume Information
      - .*RECYCLE.BIN
      - .Rproj.*
      - ^.git$
"aws_share_2":
  path: /mounts/aws_share_2
  groups:
    - test
"sedre_archive":
  path: /mounts/sedre_archive
  groups:
    - sedre
```
## **allow_deletion**
- **Type:** Boolean
- **Default value:** False
- **Description:** Indicates if studies found in non-default workspace can be deleted by the application
## **matrix_gc_sleeping_time**
- **Type:** Integer
- **Default value:** 3600 (corresponds to 1 hour)
- **Description:** Time in seconds to sleep between two garbage collections (which means matrix suppression)
## **matrix_gc_dry_run**
- **Type:** Boolean
- **Default value:** False
- **Description:** If `True`, matrices will never be removed. Else, the ones that are unused will.
## **auto_archive_sleeping_time**
- **Type:** Integer
- **Default value:** 3600 (corresponds to 1 hour)
- **Description:** Time in seconds to sleep between two auto_archiver tasks (which means zipping unused studies)
## **auto_archive_dry_run**
- **Type:** Boolean
- **Default value:** False
- **Description:** If `True`, studies will never be archived. Else, the ones that no one has accessed for a while will.
## **auto_archive_threshold_days**
- **Type:** Integer
- **Default value:** 60
- **Description:** Number of days after last study access when the study should be archived
## **auto_archive_max_parallel**
- **Type:** Integer
- **Default value:** 5
- **Description:** Max auto archival tasks in parallel
## **watcher_lock**
- **Type:** Boolean
- **Default value:** True
- **Description:** If False, it will scan without any delay. Else, its delay will be the value of the field `watcher_lock_delay`
## **watcher_lock_delay**
- **Type:** Integer
- **Default value:** 10
- **Description:** Seconds delay between two scans
## **download_default_expiration_timeout_minutes**
- **Type:** Integer
- **Default value:** 1440 (corresponds to 1 day)
- **Description:** Minutes before your study download will be cleared. The value could be less than the default one as an user should download his study pretty soon after the download becomes available.

# launcher
This section concerns the launcher used, its options and the solver binaries.
## **default**
- **Type:** String, possible values: `local` or `slurm`
- **Default value:** `local`
- **Description:** Default launcher configuration
## **local**
### **enable_nb_cores_detection**
- **Type:** Boolean
- **Default value:** False
- **Description:** Enables detection of available CPUs for the solver. If so, the default value used will be max(1, multiprocessing.cpu_count() - 2). Else, it will be 22. To maximize the solver's performance, it is recommended to activate this option.
### **binaries**
- **Type:** Dictionary
- **Default value:** Empty Dictionary
- **Description:** Binary paths for various versions of the launcher. Example:
```
700: /home/john/Antares/antares_web_data/antares-solver/antares-8.0-solver
800: /home/john/Antares/antares_web_data/antares-solver/antares-8.0-solver
810: /home/john/Antares/antares_web_data/antares-solver/antares-8.3-solver
820: /home/john/Antares/antares_web_data/antares-solver/antares-8.3-solver
830: /home/john/Antares/antares_web_data/antares-solver/antares-8.3-solver
840: /home/john/Antares/antares_web_data/antares-solver/antares-8.4-solver
850: /home/john/Antares/antares_web_data/antares-solver/antares-8.5-solver
860: /home/john/Antares/antares_web_data/antares-solver/antares-8.6-solver
```
*NB: As you can see, you can use newer solver for older study version thanks to the solver retro-compatibility*
## **slurm** 
SLURM (Simple Linux Utility for Resource Management) is used to interact with a remote environment (for Antares it's Calin) as a workload manager.
### **local_workspace**
- **Type:** Path
- **Default value:** Path()
- **Description:** Path to the local SLURM workspace
### **username**
- **Type:** String
- **Default value:** Empty String
- **Description:** Username for SLURM to connect itself with SSH protocol to Calin.
### **hostname**
- **Type:** String
- **Default value:** Empty String
- **Description:** IP address for SLURM to connect itself with SSH protocol to Calin.
### **port**
- **Type:** Integer
- **Default value:** 0
- **Description:**  SSH port for SLURM

Examples:
- Options to connect SLURM to Calin `calinfrprdif201` (production):
```
username: run-antares
hostname: 10.134.248.111
port: 22
```
- Options to connect SLURM to Calin `PF9SOCALIN019` (recette and integration):
```
username: dev-antares
hostname: 10.132.145.143
port: 22
```
### **private_key_file**
- **Type:** Path
- **Default value:** Path()
- **Description:** SSH private key file. If you do not have one, you have to fill the `password` field.
### **password**
- **Type:** String
- **Default value:** Empty String
- **Description:** SSH password for the remote server. You need it or a private key file for SLURM to connect itself.
### **key_password**
- **Type:** String
- **Default value:** Empty String
- **Description:** An optional password to use to decrypt the key file, if it's encrypted
### **default_wait_time**
*NB: Deprecated as the app is launched with wait_mode=False*
- **Type:** Integer
- **Default value:** 0
- **Description:** Default delay (in seconds) of the SLURM loop checking the status of the tasks and recovering those completed in the loop. Often used value: 900 (15 minutes)
### **default_time_limit**
- **Type:** Integer
- **Default value:** 0
- **Description:** Time_limit for SLURM jobs (in seconds). If a jobs exceed this time_limit, SLURM kills the job and it is considered failed. Often used value: 172800 (48 hours)
### **enable_nb_cores_detection**
- **Type:** Boolean
- **Default value:** False
- **Description:** Enables detection of available CPUs for the solver. It is not implemented yet but when it will, the command `sinfo` will be used via SSH to collect this information.
### **nb_cores**
#### **min**
- **Type:** Integer
- **Default value:** 1
- **Description:** Minimum amount of CPUs to use when launching a simulation.
#### **default**
- **Type:** Integer
- **Default value:** 22
- **Description:** Default amount of CPUs to use when launching a simulation. Used when not specified by the user.
#### **max**
- **Type:** Integer
- **Default value:** 24
- **Description:** Maximum amount of CPUs to use when launching a simulation.
### **default_json_db_name**
- **Type:** String
- **Default value:** Empty String
- **Description:** SLURM local DB name. Often used value : `launcher_db.json`
### **slurm_script_path**
- **Type:** String
- **Default value:** Empty String
- **Description:** Bash script path to execute on remote server.
  - If SLURM is connected to `calinfrprdif201` (production), use this path: `/applis/antares/launchAntares.sh`
  - If SLURM is connected to `PF9SOCALIN019` (recette and integration), use this path: `/applis/antares/launchAntaresRec.sh`
### **antares_versions_on_remote_server**
- **Type:** List of String
- **Default value:** Empty List
- **Description:** List of Antares solver versions available on the remote server. Examples:
```
  antares_versions_on_remote_server:
    - "800"
    - "830"
    - "840"
    - "850"
```

# logging
This section concerns the application logs
## **level**
- **Type:** String, possible values: "INFO", "WARNING", "ERROR", "DEBUG"
- **Default value:** `INFO`
- **Description:** Logging level of the application (INFO, DEBUG, etc.)
## **logfile**
- **Type:** Path
- **Default value:** None
- **Description:** Path to the application log file. Often used value : `.tmp/antarest.log`
## **json**
- **Type:** Boolean
- **Default value:** False
- **Description:** If `True`, logging format will be `JSON`, else it is `console`

# root_path
- **Type:** String
- **Default value:** Empty String
- **Description:** Root path for FastAPI. To use a remote server, use `/api` and for local environment: `api`.
"api"  

## `From now on, every section is optional`

# debug
- **Type:** Boolean
- **Default value:** False
- **Description:** If `True`, it tells the engine object to log all the SQL it executed to `sys.stdout`

# cache
## **checker_delay**
- **Type:** Float
- **Default value:** 0.2
- **Description:** Time in seconds to sleep before checking what needs to be removed from cache

# tasks
## **max_workers**
- **Type:** Integer
- **Default value:** 5
- **Description:** Number of threads for Tasks in the ThreadPoolExecutor
## **remote_workers**
- **Type:** List
- **Default value:** Empty List
- **Description:** Example:
```
remote_workers:
  -
    name: aws_share_2
    queues:
      - unarchive_aws_share_2
  -
    name: simulator_worker
    queues:
      - generate-timeseries
      - generate-kirshoff-constraints
```

# server
## **worker_threadpool_size**
- **Type:** Integer
- **Default value:** 5
- **Description:** Number of threads of the Server in the ThreadPoolExecutor
## **services**
- **Type:** List of possible Strings: "watcher", "matrix_gc", "archive_worker", "auto_archiver", "simulator_worker"
- **Default value:** Empty List
- **Description:** # Services to enable when launching the application

# redis
This sections concerns the redis backend to handle eventbus. It is recommended to use it in production but not for local environment.
## **host**
- **Type:** String
- **Default value:** `localhost`
- **Description:** Redis server hostname
## **port**
- **Type:** Integer
- **Default value:** 6379
- **Description:** Redis server port
## **password**
- **Type:** String
- **Default value:** None
- **Description:** Redis password