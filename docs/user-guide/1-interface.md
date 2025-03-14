---
title: User Interface
author: Antares Web Team
date: 2021-11-03
category: User Guide
tags:

  - ui
  - job
  - api
  - token
  - variant
  - matrix
  - dataset
  - batch
  - launch
  - settings
---

# User interface

## What's new (2.18.0)
- redesign of the debug view, with the possibility of importing files into the user folder. See more details [here](./study/05-debug.md)
- new endpoint for admin to clear snapshots
- update version of python to 3.11
- time series generator for thermals clusters. See more details [here](../user-guide/simulation-configuration/all-configurations.md#time-series-management)
- installer for desktop version of Antares Web
- use .7z format to export and archive studies
- new component for matrix (Data Glide)
- adding column filters and search bar on results view
- enhance results columns headers
- adding aggregates columns on some matrix
- disable copy/paste on matrix 
- allow csv import
- allow to change app language. See more details [here](#tabs-description)

Antares Web is supporting antares simulator version untill v8.8.x.
For more details, see the changelog.

## Main features of the interface

- [Launch batch mode](#launch-batch-mode)
- [Strict folder filtering](#strict-folder-filtering)
- [Zipped output retrieval](#launch-dialog)

The application is split into 3 main menus: Studies, Jobs, and Data.
API documentation, external reference links, and user account details are also available.

- "Studies" is the main section and redirects to the study listing where we can browse studies and work on them.
- "Jobs" is a monitoring section that displays currently running or latest execution jobs.
- "Data" is a section where we can manage matrix data that can then be used in
  the [variant manager](#variant-management).

![](../assets/media/img/userguide_mainmenu.png)

## Study listing

The study listing view is the main view, which provides :

- the listing of existing studies
- filters/sorting/tree view
- creation/import tool

Studies are linked to a "workspace" which refers to a storage disk. The workspace "default" (orange colored) is
the internal storage where "managed" studies live. These studies files aren't meant to be accessible directly (via disk
mount for instance).  
The other workspaces are studies that are found on mounted workspace and their unique ID can change if the studies are
moved.

Copied studies are always copied within the managed workspace. These managed studies though not directly accessible
offers additional features:

- a permanent ID
- archiving
- variant creation
- faster operations
- storage improvements

![](../assets/media/img/userguide_studylisting.png)

Some actions are available from this view:

- launching the study simulation
- exporting the study
- deleting the study

![](../assets/media/img/userguide_studyactions.png)

### Launch Dialog

When launching a study, a dialog will open with some choices.

![](../assets/media/img/userguide_launch_dialog.png)

### Launch batch mode

To launch multiple studies at once, we can click on the checkbox icon to enable selection mode. In this mode, we can
click
on study cards to select / unselect them. Then clicking on the launch button will open
the launch dialog.

![](../assets/media/img/userguide_batch_launch.png)

### Strict folder filtering

The folder icon next to the breadcrumb path allow to filter (when activated) the studies to only the direct descendant
of the selected folder.

![](../assets/media/img/userguide_strict_folder_filter.png)

For more operation over a study, we can click on a study "explore" button and go to the dedicated study view.
The url of dedicated study view can be bookmarked for sharing or quick access.

## Study view

The study view is composed of 2 or 3 main menus depending on the managed status of the study.

- ["Information"](#overview) view is an overview of the study
- ["Detailed view"](#detailed-view) is a raw view of the study contents
- ["Variant"](#variant-management) view is where we can manage the variant of a study if it is managed

### Overview

The overview provides access to :

- basic metadata
- name and permission edition (a study can be public or associated with groups with specific permissions)
- simulation execution monitoring
- variant dependency tree

![](../assets/media/img/userguide_studyoverview.png)

### Variant management

The variant command tab is only available for managed variant studies.  
It shows an edition view where we can:

- edit the command list composing the variant
- monitor or verify the result of the generation process

![](../assets/media/img/userguide_variantcommands.png)

### Detailed view

The detailed view is a tree representation of a study files.
It can be browsed and node can be viewed and edited.  
:warning: The view can take some time to load the first time.

Example of the detailed view of a configuration node (ini files):

![](../assets/media/img/userguide_treeview_json.png)

Example of the detailed view of a matrix node (txt data files):

![](../assets/media/img/userguide_treeview_matrix.png)

## Data management

The data view display dataset which are list of matrices.
These matrices can then be used as argument in [variant manager commands](./3-variant_manager.md#command-list).

![](../assets/media/img/userguide_dataset_listing.png)

The data which can be uploaded are either a single tsv file, or a zipped list of tsv matrix files.

![](../assets/media/img/userguide_dataset_creation.png)

## Settings

The settings are accessible in the menu on the left of the application. There are a total of 5 tabs that are visible depending on the user profile:
- the normal user has access to GENERAL and TOKENS tabs
- the administrator user of a group has access to the GROUPS tab in addition to the normal user tabs
- the server administrator has access to all tabs (USERS and MAINTENANCE tabs in addition to the others).

### Tabs description
1. GENERAL: allows you to change the language of the application, two possible choices English or French
2. USERS: List of users on the server, you can create, delete or modify their permissions
3. GROUPS: List of user groups on the server, you can create, delete, modify its list of users or their permissions in the group
4. TOKENS: Allows you to create a token that will be used to access to APIs via scripts
5. MAINTENANCE: Allows you to put the server in maintenance mode, preventing other users other than the administrator from accessing the application. 

![userguide_change_language.png](../assets/media/img/userguide_change_language.png)

### Create a token

These token can be used in scripts that will use the [API](#api-documentation).

![](../assets/media/img/userguide_token_listing.png)

We can choose to assign specific permission to the token and can choose if the scripts using the token will impersonate
our user or not.
If we choose the later, studies created using the token will be owned by a new user that will have the token's name.

![](../assets/media/img/userguide_token_creation.png)

We have to save the token (as it is generated once and not saved). It will then be used as an authentication token in
HTTP Basic Auth, eg.:

```
curl -H 'Authorization: Bearer <my_token_string>' https://antares-web/api/studies
```

![](../assets/media/img/userguide_token_result.png)

## API Documentation

The API documentation is an interactive documentation of HTTP endpoints that can be used to operate with the server.

![](../assets/media/img/userguide_apidoc.png)
