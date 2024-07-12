[![Status][ci_result]][ci_result_link] [![Quality Gate Status][coverage_result]][coverage_result_link] [![License][license_badge]][license_link]

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![TypeScript](https://img.shields.io/badge/TypeScript-00599c?style=for-the-badge&logo=TypeScript&logoColor=61DAFB)
![React](https://img.shields.io/badge/React-00599c?style=for-the-badge&logo=react&logoColor=61DAFB)

![](assets/antares.png "Antares Web Logo")
> Web API and UI for [Antares Simulator][antares-simulator-website]

Please see the [Antares Web Documentation][antares-web-readthedocs] for an introductory tutorial,
and a full user guide. Visit the [Antares-Simulator Documentation][antares-simulator-readthedocs] for more insights on
ANTARES.

## Introduction

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

## Documentation

- [Building the application](./install/0-INSTALL.md)
- [Using the application](./user-guide/0-introduction.md)
- [Contributing to the application code](./architecture/0-introduction.md)

`Antares-Web` is currently under development. Feel free to submit any issue.

[ci_result]: https://github.com/AntaresSimulatorTeam/AntaREST/actions/workflows/main.yml/badge.svg

[ci_result_link]: https://github.com/AntaresSimulatorTeam/AntaREST/actions/workflows/main.yml

[coverage_result]: https://sonarcloud.io/api/project_badges/measure?project=AntaresSimulatorTeam_api-iso-antares&metric=coverage

[coverage_result_link]: https://sonarcloud.io/dashboard?id=AntaresSimulatorTeam_api-iso-antares

[license_badge]: https://img.shields.io/github/license/AntaresSimulatorTeam/AntaREST

[license_link]: https://www.apache.org/licenses/LICENSE-2.0

[antares-web-readthedocs]: https://antares-web.readthedocs.io/

[antares-simulator-readthedocs]: https://antares-simulator.readthedocs.io/

[antares-simulator-website]: https://antares-simulator.org

[antares-simulator-github]: https://github.com/AntaresSimulatorTeam/Antares_Simulator
