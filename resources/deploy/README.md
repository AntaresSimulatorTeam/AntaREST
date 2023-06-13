# Antares Web

> WARNING: in Linux environment, the following files must be executable.
> To do this, you can run the following commands:
>
> ```shell
> chmod +x AntaresWeb/AntaresTool
> chmod +x AntaresWeb/AntaresWebServer
> chmod +x AntaresWebWorker
> ```

To launch the Antares Web, run the command:

```shell
./AntaresWeb/AntaresWebServer
```

Then go to http://127.0.0.1:8080

## Variant manager tool

To use the variant manager tool, run the command:

```
./AntaresWeb/AntaresTool --help
```

Further instruction will be provided by the command output.

## Archive worker

The Antares archive manager is a command that runs in the background to automatically unarchive simulation results.
The worker is notified by the web application via EventBus to initiate asynchronous unarchiving of the results.

To launch the archive worker, run the command:

```
./AntaresWebWorker -c config.yaml -w default
```

Further instructions can be found in the online help. Use the `--help' option.
