# Introduction

![](../assets/antares.png)

This package works along with RTE's adequacy software [Antares Simulator](https://antares-simulator.org) that is also [hosted on github][antares-github]

`antares-web` is a server api interfacing Antares Simulator studies. It provides a web application to manage studies
adding more features to simple edition.

This brings:

> - **application interoperability** : assign unique id to studies, expose operation endpoint api
>
> - **optimized storage**: extract matrices data and share them between studies, archive mode
>
> - **variant management**: add a new editing description language and generation tool
>
> - **user accounts** : add user management and permission system


## Variant manager

`antares-web` brings an edition event store that provides a way to edit a study while keeping track of changes.
It eases the creation of "variants" of a study and allow an explicit diff change between studies.

You can read more information in [using the variant manager here](./2-variant_manager.md)