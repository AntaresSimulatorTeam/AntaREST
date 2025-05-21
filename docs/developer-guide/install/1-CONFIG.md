# Application Configuration Documentation

In the following, we will be exploring how to edit your application configuration file. <br>
As explained in the main documentation readme file, you can use the following command line 
to start the API:

```shell
python3 antarest/main.py -c resources/application.yaml --auto-upgrade-db --no-front
```

The `-c` option here describes the path towards the configuration `.yaml` file. If this option is 
not fed to the program, it will to look for files in the following locations (in order):

1. `./config.yaml`
2. `../config.yaml`
3. `$HOME/.antares/config.yaml`

<br>
In this documentation, you will have a global overview of the configuration 
file structure and details for each of the `.yaml` fields with specifications regarding
type of data and the default values, and descriptions of those fields.


# File Structure

- [Security](#security)
- [Database](#db)
- [Storage](#storage)
- [Launcher](#launcher)
- [Logging](#logging)
- [Root Path](#root_path)
- [Optional sections](#debug)

# security

This section defines the settings for application security, authentication, and groups.

## **disabled**

- **Type:** Boolean
- **Default value:** false
- **Description:** If set to `false`, user identification will be required when launching the app.

## **jwt**

### **key**

- **Type:** String (usually a Base64-encoded one)
- **Default value:** ""
- **Description:** JWT (Json Web Token) secret key for authentication.

## **login**

### **admin**

#### **pwd**

- **Type:** String
- **Default value:** ""
- **Description:** Admin user's password.

## **external_auth**

This subsection is about setting up an external authentication service that lets you connect to an LDAP using a web
service. The group names and their IDs are obtained from the LDAP directory.

### **url**

- **Type:** String
- **Default value:** ""
- **Description:** External authentication URL. If you want to enable local authentication, you should write "".

### **default_group_role**

- **Type:** Integer
- **Default value:** 10
- **Description:** Default user role for external authentication
    - `ADMIN = 40`
    - `WRITER = 30`
    - `RUNNER = 20`
    - `READER = 10`

### **add_ext_groups**

- **Type:** Boolean
- **Default value:** false
- **Description:** Whether to add external groups to user roles.

### **group_mapping**

- **Type:** Dictionary
- **Default value:** {}
- **Description:** Groups of the application: Keys = Ids, Values = Names. Example:
    - 00000001: espace_commun
    - 00001188: drd
    - 00001574: cnes

```yaml
# example for security settings
security:
  disabled: false
  jwt:
    key: best-key
  login:
    admin:
      pwd: root
  external_auth:
    url: ""
    default_group_role: 10
    group_mapping:
      id_ext: id_int
    add_ext_groups: false
```

# db

This section presents the configuration of application's database connection.

## **url**

- **Type:** String
- **Default value:** ""
- **Description:** The Database URL. For example, `sqlite:///database.db` for a local SQLite DB
  or `postgresql://postgres_user:postgres_password@postgres_host:postgres_port/postgres_db` for a PostgreSQL DB.

## **admin_url**

- **Type:** String
- **Default value:** None
- **Description:** The URL you can use to directly access your database.

## **pool_use_null**

- **Type:** Boolean
- **Default value:** false
- **Description:** If set to `true`, connections are not pooled. This parameter should be kept at `false` to avoid
  issues.

## **db_connect_timeout**

- **Type:** Integer
- **Default value:** 10
- **Description:** The timeout (in seconds) for database connection creation.

## **pool_recycle**

- **Type:** Integer
- **Default value:** None
- **Description:** Prevents the pool from using a particular connection that has passed a certain time in seconds. An
  often-used value is 3600, which corresponds to an hour. *Not used for SQLite DB.*

## **pool_size**

- **Type:** Integer
- **Default value:** 5
- **Description:** The maximum number of permanent connections to keep. *Not used for SQLite DB.*

## **pool_use_lifo**

- **Type:** Boolean
- **Default value:** false
- **Description:** Specifies whether the Database should use the Last-in-First-out method. It is commonly used in cases
  where the most recent data entry is the most important and applies to the application context. Therefore, it's better
  to set this parameter to `true`. *Not used for SQLite DB.*

## **pool_pre_ping**

- **Type:** Boolean
- **Default value:** false
- **Description:** Connections that are closed from the server side are gracefully handled by the connection pool and
  replaced with a new connection. *Not used for SQLite DB.*

## **pool_max_overflow**

- **Type:** Integer
- **Default value:** 10
- **Description:** Temporarily exceeds the set pool_size if no connections are available. *Not used for SQLite DB.*

```yaml
# example for db settings
db:
  url: "postgresql://postgres:My:s3Cr3t/@127.0.0.1:30432/antares"
  admin_url: "postgresql://{{postgres_owner}}:{{postgres_owner_password}}@{{postgres_host}}:{{postgres_port}}/{{postgres_db}}"
  pool_recycle: 3600
  pool_max_overflow: 10
  pool_size: 5
  pool_use_lifo: true
  pool_use_null: false
```

# storage

The following section configuration parameters define the application paths and services options.

## **tmp_dir**

- **Type:** Path
- **Default value:** `tempfile.gettempdir()` (
  documentation [here](https://docs.python.org/3/library/tempfile.html#tempfile.gettempdir))
- **Description:** The temporary directory for storing temporary files. An often-used value is `./tmp`.

## **matrixstore**

- **Type:** Path
- **Default value:** `./matrixstore`
- **Description:** Antares Web extracts matrices data and shares them between managed studies to save space. These
  matrices are stored here.

## **archive_dir**

- **Type:** Path
- **Default value:** `./archives`
- **Description:** The directory for archived (zipped) studies.

## **workspaces**

- **Type:** Dictionary
- **Default value:** {}
- **Description:** Different workspaces where the application expects to find studies. Keys = Folder names, Values =
  WorkspaceConfig object. Such an object has 4 fields:
    - `groups`: List of groups corresponding to the workspace (default [])
    - `path`: Path of the workspace (default `Path()`)
    - `filter_in`: List of regex. If a folder does not contain a file whose name matches one of the regex, it's not
      scanned (default [".*"])
    - `filter_out`: List of regex. If a folder contains any file whose name matches one of the regex, it's not scanned (
      default [])

> NOTE: If a directory is to be ignored by the watcher, place a file named `AW_NO_SCAN` inside.

Examples:

```yaml
default:
  path: /home/john/Projects/antarest_data/internal_studies/
studies:
  path: /home/john/Projects/antarest_data/studies/
staging_studies:
  path: /home/john/Projects/antarest_data/staging_studies/
```

```yaml
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
    - ^areas$
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
- **Default value:** false
- **Description:** Indicates if studies found in non-default workspace can be deleted by the application.

## **matrix_gc_sleeping_time**

- **Type:** Integer
- **Default value:** 3600 (corresponds to 1 hour)
- **Description:** Time in seconds to sleep between two garbage collections (which means matrix suppression).

## **matrix_gc_dry_run**

- **Type:** Boolean
- **Default value:** false
- **Description:** If `true`, matrices will never be removed. Else, the ones that are unused will.

## **auto_archive_sleeping_time**

- **Type:** Integer
- **Default value:** 3600 (corresponds to 1 hour)
- **Description:** Time in seconds to sleep between two auto_archiver tasks (which means zipping unused studies).

## **auto_archive_dry_run**

- **Type:** Boolean
- **Default value:** false
- **Description:** If `true`, studies will never be archived. Else, the ones that no one has accessed for a while will.

## **auto_archive_threshold_days**

- **Type:** Integer
- **Default value:** 60
- **Description:** Number of days after the last study access date before it should be archived.

## **auto_archive_max_parallel**

- **Type:** Integer
- **Default value:** 5
- **Description:** Max auto archival tasks in parallel.

## **snapshot_retention_days**

- **Type:** Integer
- **Default value:** 7
- **Description:** Snapshots of variant not updated or accessed for **snapshot_retention_days** days will be cleared.

## **watcher_lock**

- **Type:** Boolean
- **Default value:** true
- **Description:** If false, it will scan without any delay. Else, its delay will be the value of the
  field `watcher_lock_delay`.

## **watcher_lock_delay**

- **Type:** Integer
- **Default value:** 10
- **Description:** Seconds delay between two scans.

## **download_default_expiration_timeout_minutes**

- **Type:** Integer
- **Default value:** 1440 (corresponds to 1 day)
- **Description:** Minutes before your study download will be cleared. The value could be less than the default one as a
  user should download his study pretty soon after the download becomes available.

## **matrixstore_format**

- **Type:** String, possible values: `tsv`, `hdf`, `parquet` or `feather`
- **Default value:** `tsv`
- **Description:** Matrixstore internal storage format. `tsv` is the Antares studies format but to improve performance
and to reduce the disk space allocated to these matrices, you can choose other formats supported by the app. 
It doesn't impact users as it's for internal usage only, matrices will be displayed the same way no matter the format.


```yaml
# example for storage settings
storage:
  tmp_dir: /home/jon/Projects/antarest_data/tmp
  matrixstore: /home/jon/Projects/antarest_data/matrices
  archive_dir: /home/jon/Projects/antarest_data/archives
  allow_deletion: false
  matrix_gc_sleeping_time: 3600
  matrix_gc_dry_run: False
  workspaces:
    default:
      path: /home/jon/Projects/antarest_data/internal_studies/
    studies:
      path: /home/jon/Projects/antarest_data/studies/
    staging_studies:
      path: /home/jon/Projects/antarest_data/staging_studies/
```

# launcher

This section provides the launcher with specified options and defines the settings for solver binaries.

## **default**

- **Type:** String, possible values: `local` or `slurm`
- **Default value:** `local`
- **Description:** Default launcher configuration, if set to `local` then the launcher is defined locally. Otherwise
it is instantiated on shared servers using `slurm`.

## **local**

### **enable_nb_cores_detection**

- **Type:** Boolean
- **Default value:** false
- **Description:** Enables detection of available CPUs for the solver. If so, the default value used will be `max(1,
  multiprocessing.cpu_count() - 2)`. Else, it will be 22. To maximize the solver's performance, it is recommended to
  activate this option.

### **binaries**

- **Type:** Dictionary
- **Default value:** {}
- **Description:** Binary paths for various versions of the launcher. Example:

```yaml
700: /home/john/Antares/antares_web_data/antares-solver/antares-8.0-solver
800: /home/john/Antares/antares_web_data/antares-solver/antares-8.0-solver
810: /home/john/Antares/antares_web_data/antares-solver/antares-8.3-solver
820: /home/john/Antares/antares_web_data/antares-solver/antares-8.3-solver
830: /home/john/Antares/antares_web_data/antares-solver/antares-8.3-solver
840: /home/john/Antares/antares_web_data/antares-solver/antares-8.4-solver
850: /home/john/Antares/antares_web_data/antares-solver/antares-8.5-solver
860: /home/john/Antares/antares_web_data/antares-solver/antares-8.6-solver
```

> NOTE: As you can see, you can use newer solver for older study version thanks to the solver retro-compatibility

### **xpress_dir**

- **Type:** str
- **Default value:** None
- **Description:** Path towards your xpress_dir. Needed if you want to launch a study with xpress. If the environment 
variables "XPRESS_DIR" and "XPRESS" are set on your local environment it should work without setting them.

### **local_workspace**

- **Type:** Path
- **Default value:** `./local_workspace`
- **Description:** Antares Web uses this directory to run the simulations.

## **slurm**

SLURM (Simple Linux Utility for Resource Management) is used to interact with a remote environment (for Antares it's
computing server) as a workload manager.

### **local_workspace**

- **Type:** Path
- **Default value:** Path
- **Description:** Path to the local SLURM workspace

### **username**

- **Type:** String
- **Default value:** ""
- **Description:** Username for SLURM to connect itself with SSH protocol to computing server.

### **hostname**

- **Type:** String
- **Default value:** ""
- **Description:** IP address for SLURM to connect itself with SSH protocol to computing server.

### **port**

- **Type:** Integer
- **Default value:** 0
- **Description:**  SSH port for SLURM

Examples:

- Options to connect SLURM to computing server `prod-server-name` (production):

```
username: run-antares
hostname: XX.XXX.XXX.XXX
port: 22
```

- Options to connect SLURM to computing server `dev-server-name` (recette and integration):

```
username: dev-antares
hostname: XX.XXX.XXX.XXX
port: 22
```

### **private_key_file**

- **Type:** Path
- **Default value:** Path()
- **Description:** SSH private key file. If you do not have one, you have to fill the `password` field.

### **password**

- **Type:** String
- **Default value:** ""
- **Description:** SSH password for the remote server. You need it or a private key file for SLURM to connect itself.

### **key_password**

- **Type:** String
- **Default value:** ""
- **Description:** An optional password to use to decrypt the key file, if it's encrypted

### **default_wait_time**

> NOTE: Deprecated as the app is launched with wait_mode=false*

- **Type:** Integer
- **Default value:** 0
- **Description:** Default delay (in seconds) of the SLURM loop checking the status of the tasks and recovering those
  completed in the loop. Often used value: 900 (15 minutes)

### **default_time_limit**

- **Type:** Integer
- **Default value:** 0
- **Description:** Time limit for SLURM jobs (in seconds). If a jobs exceed this time limit, SLURM kills the job and it
  is considered failed. Often used value: 172800 (48 hours)

### **enable_nb_cores_detection**

- **Type:** Boolean
- **Default value:** false
- **Description:** Enables detection of available CPUs for the solver (Not implemented yet).

### **nb_cores**

#### **min**

- **Type:** Integer
- **Default value:** 1
- **Description:** Minimum amount of CPUs to use when launching a simulation.

#### **default**

- **Type:** Integer
- **Default value:** 22
- **Description:** Default amount of CPUs to use when launching a simulation. The user can override this value in the
  launch dialog box.

#### **max**

- **Type:** Integer
- **Default value:** 24
- **Description:** Maximum amount of CPUs to use when launching a simulation.

### **default_json_db_name**

- **Type:** String
- **Default value:** ""
- **Description:** SLURM local DB name. Often used value : `launcher_db.json`

### **slurm_script_path**

- **Type:** String
- **Default value:** ""
- **Description:** Bash script path to execute on remote server.
    - If SLURM is connected to `prod-server-name` (*production*), use this path: `/applis/antares/launchAntares.sh`
    - If SLURM is connected to `dev-server-name` (*recette* and *integration*), use this
      path: `/applis/antares/launchAntaresRec.sh`

### **partition**

- **Type:** String
- **Default value:** ""
- **Description:** SLURM partition name. The partition refers to a logical division of the computing resources
  available on a cluster managed by SLURM.
  - If not specified, the default behavior is to allow the SLURM controller
    to select the default partition as designated by the system administrator.

### **antares_versions_on_remote_server**

- **Type:** List of String
- **Default value:** []
- **Description:** List of Antares solver versions available on the remote server. Examples:

```yaml
# example for launcher settings
launcher:
  default: local
  launchers:
    - id: local
      name: my_local
      type: local
      binaries:
        860: /home/jon/opt/antares-solver_ubuntu20.04/antares-8.6-solver
    - id: slurm
      name: my_slurm
      type: slurm
      local_workspace: /home/jon/Projects/antarest_data/slurm_workspace
      username: jon
      hostname: localhost
      port: 22
      private_key_file: /home/jon/.ssh/id_rsa
      key_password:
      default_wait_time: 900
      default_time_limit: 172800
      default_n_cpu: 20
      default_json_db_name: launcher_db.json
      slurm_script_path: /applis/antares/launchAntares.sh
      partition: calin1
      db_primary_key: name
      antares_versions_on_remote_server:
        - '610'
        - '700'
```

# Logging

This section sets the configuration for the application logs.

## **level**

- **Type:** String, possible values: "DEBUG", "INFO", "WARNING", "ERROR"
- **Default value:** `INFO`
- **Description:** The logging level of the application (INFO, DEBUG, etc.).

## **logfile**

- **Type:** Path
- **Default value:** None
- **Description:** The path to the application log file. An often-used value is `.tmp/antarest.log`.

## **json**

- **Type:** Boolean
- **Default value:** false
- **Description:** If `true`, the logging format will be `json`; otherwise, it is `console`.
    - `console`: The default format used for console output, suitable for Desktop versions or development environments.
    - `json`: A specific JSON format suitable for consumption by monitoring tools via a web service.

```yaml
# example for logging settings
logging:
  level: INFO
  logfile: ./tmp/antarest.log
  json: false
```

# root_path

- **Type:** String
- **Default value:** ""
- **Description:** The root path for FastAPI. To use a remote server, use `/api`, and for a local environment: `api`.

```yaml
# example for root_path settings
root_path: "/{root_path}"

```

## `Extra optional configuration`

# debug

- **Type:** Boolean
- **Default value:** false
- **Description:** This flag determines whether the engine will log all the SQL statements it executes to the console.
  If you turn this on by setting it to `true`, you'll see a detailed log of the database queries.

```yaml
# example for debug settings
debug: false
```

# cache

## **checker_delay**

- **Type:** Float
- **Default value:** 0.2
- **Description:** The time in seconds to sleep before checking what needs to be removed from the cache.

```yaml
# example for cache settings
cache:
  checker_delay: 0.2
```

# tasks

## **max_workers**

- **Type:** Integer
- **Default value:** 5
- **Description:** The number of threads for Tasks in the ThreadPoolExecutor.

## **remote_workers**

- **Type:** List
- **Default value:** []
- **Description:** Example:

```yaml
# example for tasks settings
tasks:
  max_workers: 4
  remote_workers:
    - name: aws_share_2
      queues:
        - unarchive_aws_share_2
    - name: simulator_worker
      queues:
        - generate-timeseries
        - generate-kirshoff-constraints
```

# server

## **worker_threadpool_size**

- **Type:** Integer
- **Default value:** 5
- **Description:** The number of threads of the Server in the `ThreadPoolExecutor`.

## **services**

- **Type:** List of Strings
- **Default value:** []
- **Description:** Services to enable when launching the application. Possible values: "watcher," "matrix_gc," "
  archive_worker," "auto_archiver," "simulator_worker."

```yaml
#example for server settings
server:
  worker_threadpool_size: 5
  services:
    - watcher
    - matrix_gc
```

# redis

This section is for the settings of Redis backend, which is used for managing the event bus and in-memory caching.

## **host**

- **Type:** String
- **Default value:** `localhost`
- **Description:** The Redis server hostname.

## **port**

- **Type:** Integer
- **Default value:** 6379
- **Description:** The Redis server port.

## **password**

- **Type:** String
- **Default value:** None
- **Description:** The Redis password.

```yaml
# example for redis settings
redis:
  host: localhost
  port: 9862
```