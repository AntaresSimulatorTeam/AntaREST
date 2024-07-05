---
title: Introduction to Antares Web
author: Antares Web Team
date: 2021-10-05
category: User Guide
tags:

  - introduction
  - variant
  - solver
  - manager

---

# Introduction

![](../assets/antares.png "Antares Web Logo")

Welcome to `antares-web`, a comprehensive web application designed to interface with RTE’s adequacy software,
the [Antares Simulator][antares-simulator-website], also [hosted on GitHub][antares-simulator-github].
The Antares Simulator is an open-source power system simulator for anyone valuing the quantification of adequacy or the
economic performance of interconnected energy systems over short or distant time horizons.
It enables detailed modeling of energy consumption, generation, and transportation, performing probabilistic simulations
across numerous year-long scenarios, each consisting of 8760 hourly time-frames.

`antares-web` serves as a server API interfacing with Antares Simulator studies, providing a web application to manage
studies while adding features for enhanced edition capabilities.

This integration brings:

- **Application Interoperability**: Assign unique IDs to studies and expose operations through an endpoint API,
  facilitating integration with other applications and services.
- **Optimized Storage**: Extract matrices data and share them between studies, supporting archive mode.
- **Variant Management**: Introduce a new editing description language and generation tool.
- **User Accounts**: Implement user management and permission systems.

## Variant Manager

`antares-web` introduces an edition event store that tracks changes, simplifying the creation of study "variants" and
allowing for explicit diff change comparisons between studies.

Explore the suite of features `antares-web` offers to enhance the Antares Simulator, improving study management,
interoperability, and user collaboration.


[antares-simulator-website]: https://antares-simulator.org

[antares-simulator-github]: https://github.com/AntaresSimulatorTeam/Antares_Simulator
