# Antares Web

## Launching the Web Server

### Windows

To launch the Antares Web server on Windows, follow these steps:

1. Use the provided `AntaresWebServerShortcut.lnk` shortcut.
2. Ensure that no previous version of the server is running. If it is, locate the "AntaresWebServer" icon in the system
   tray and click on it. From the menu, select "Quit".

### Ubuntu

To launch the Antares Web server on Ubuntu, follow these steps:

1. Open a terminal.
2. Navigate to the directory where the `AntaresWebServer` script is located. For example, if it is located in
   the `AntaresWeb` directory, use the following command:

```shell
cd /path/to/AntaresWeb
```

Run the following command to launch the server:

```shell
./AntaresWeb/AntaresWebServer
```

## Accessing the Web Server

Once the Antares Web server is running, the default web browser will automatically open to the application home page.
You can also manually access by following these steps:

1. Open a web browser.
2. Enter the following URL in the address bar:

```
http://127.0.0.1:8080
```

This will connect you to the Antares Web server.
