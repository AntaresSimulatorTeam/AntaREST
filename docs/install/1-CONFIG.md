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
- [Database](#db)
- [Storage](#storage)
- [Launcher](#launcher)
- [Logging](#logging)
- [Root Path](#root_path)
- [Optional sections](#debug)

# security

This section concerns application security, authentication, and groups.

## **disabled**

- **Type:** Boolean
- **Default value:** false
- **Description:** If the value is `false`, user identification is required when launching the app.

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
- **Description:** External authentication URL. If you want to enable local authentication, you should write "". To
  enable authentication via RTE "NNI", you should register http://antarestgaia:8080.

### **default_group_role**

- **Type:** Integer
- **Default value:** 10
- **Description:** Default user role for external authentication. ADMIN = 40, WRITER = 30, RUNNER = 20, READER = 10.

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

# db

This section relates to configuring the application's database connection.

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
- **Description:** If set to `true`, the Pool does not pool connections. This parameter should stay at `false` to avoid
  issues.

## **db_connect_timeout**

- **Type:** Integer
- **Default value:** 10
- **Description:** The timeout (in seconds) for database connection creation.

## **pool_recycle**

- **Type:** Integer
- **Default value:** None
- **Description:** Prevents the pool from using a particular connection that has passed a certain time in seconds. An
  often-used value is 3600, which corresponds to a day. *Not used for SQLite DB.*

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

# storage

This section concerns application Paths and Services options.

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
- **Description:** Number of days after the last study access when the study should be archived.

## **auto_archive_max_parallel**

- **Type:** Integer
- **Default value:** 5
- **Description:** Max auto archival tasks in parallel.

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

# launcher

This section concerns the launcher used, its options and the solver binaries.

## **default**

- **Type:** String, possible values: `local` or `slurm`
- **Default value:** `local`
- **Description:** Default launcher configuration

## **local**

### **enable_nb_cores_detection**

- **Type:** Boolean
- **Default value:** false
- **Description:** Enables detection of available CPUs for the solver. If so, the default value used will be max(1,
  multiprocessing.cpu_count() - 2). Else, it will be 22. To maximize the solver's performance, it is recommended to
  activate this option.

### **binaries**

- **Type:** Dictionary
- **Default value:** {}
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

> NOTE: As you can see, you can use newer solver for older study version thanks to the solver retro-compatibility

## **slurm**

SLURM (Simple Linux Utility for Resource Management) is used to interact with a remote environment (for Antares it's
Calin) as a workload manager.

### **local_workspace**

- **Type:** Path
- **Default value:** Path()
- **Description:** Path to the local SLURM workspace

### **username**

- **Type:** String
- **Default value:** ""
- **Description:** Username for SLURM to connect itself with SSH protocol to Calin.

### **hostname**

- **Type:** String
- **Default value:** ""
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
- **Description:** Time_limit for SLURM jobs (in seconds). If a jobs exceed this time_limit, SLURM kills the job and it
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
    - If SLURM is connected to `calinfrprdif201` (production), use this path: `/applis/antares/launchAntares.sh`
    - If SLURM is connected to `PF9SOCALIN019` (recette and integration), use this
      path: `/applis/antares/launchAntaresRec.sh`

### **antares_versions_on_remote_server**

- **Type:** List of String
- **Default value:** []
- **Description:** List of Antares solver versions available on the remote server. Examples:

```
  antares_versions_on_remote_server:
    - "800"
    - "830"
    - "840"
    - "850"
```

# Logging

This section concerns the application logs.

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

# root_path

- **Type:** String
- **Default value:** ""
- **Description:** The root path for FastAPI. To use a remote server, use `/api`, and for a local environment: `api`.

## `Extra optional configuration`

# debug

- **Type:** Boolean
- **Default value:** false
- **Description:** This flag determines whether the engine will log all the SQL statements it executes to the console.
  If you turn this on by setting it to `true`, you'll see a detailed log of the database queries.

# cache

## **checker_delay**

- **Type:** Float
- **Default value:** 0.2
- **Description:** The time in seconds to sleep before checking what needs to be removed from the cache.

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
- **Description:** The number of threads of the Server in the ThreadPoolExecutor.

## **services**

- **Type:** List of Strings
- **Default value:** []
- **Description:** Services to enable when launching the application. Possible values: "watcher," "matrix_gc," "
  archive_worker," "auto_archiver," "simulator_worker."

# redis

This section concerns the Redis backend, which is used for managing the event bus and in-memory caching.

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