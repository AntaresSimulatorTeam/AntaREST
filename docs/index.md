<div style="display: flex; align-items: center; margin-bottom: 30px; justify-content: center;">
  <img
    src="assets/antares.svg"
    alt="Antares Logo"
    style="height: 150px; width: 150px; margin-right: 30px;"
  />
  <div>
    <h1 style="margin: 0;">Antares Web</h1>
    <p style="margin: 5px 0 0 0; font-size: 1.2em; color: #666;">
      REST API and web interface for Antares
    </p>
  </div>
</div>


[![Status][ci_result]][ci_result_link] [![Quality Gate Status][coverage_result]][coverage_result_link] [![License][license_badge]][license_link]

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![TypeScript](https://img.shields.io/badge/TypeScript-00599c?style=for-the-badge&logo=TypeScript&logoColor=61DAFB)
![React](https://img.shields.io/badge/React-00599c?style=for-the-badge&logo=react&logoColor=61DAFB)


This site is dedicated to the **technical documentation of Antares Web.**
If you want a user guide on using Antares Web, please see the 
[centralized documentation for Antares](https://antares-doc.readthedocs.io/en/latest/).
It provides a first approach on the software and some tutorials.

## Antares Web in Antares

Welcome to Antares Web, a comprehensive web application designed to interface with 
[RTE](https://www.rte-france.com/en/home)’s adequacy software,
[Antares Simulator][antares-simulator-github].
Together, they are part of a comprehensive open-source power system simulation solution 
for anyone valuing the quantification of adequacy or the
economic performance of interconnected energy systems over short or distant time horizons.
It enables detailed modeling of energy consumption, generation, and transportation, performing probabilistic simulations
across numerous year-long scenarios, each consisting of 8760 hourly time-frames.

Antares Web serves as a server API interfacing with Antares Simulator studies,
providing a web application to manage studies while adding features 
for enhanced edition capabilities.

This integration brings:

- **Application Interoperability**: Assign unique IDs to studies and expose operations through an endpoint API,
  facilitating integration with other applications and services.
- **Optimized Storage**: Extract matrices data and share them between studies, supporting archive mode.
- **Variant Management**: Introduce a new editing description language and generation tool.
- **User Accounts**: Implement user management and permission systems.

Antares Web is developed mainly in **Python** and uses [FastAPI](https://fastapi.tiangolo.com/) web framework.
The front end is a [React](https://reactjs.org/) web application.

## Contributing

Antares Web is currently under development. Feel free to 
[submit any issue](https://github.com/AntaresSimulatorTeam/AntaREST/issues).
You can also contribute to the code (see [contribution guide](./CONTRIBUTING.md)).


[ci_result]: https://github.com/AntaresSimulatorTeam/AntaREST/actions/workflows/main.yml/badge.svg

[ci_result_link]: https://github.com/AntaresSimulatorTeam/AntaREST/actions/workflows/main.yml

[coverage_result]: https://sonarcloud.io/api/project_badges/measure?project=AntaresSimulatorTeam_api-iso-antares&metric=coverage

[coverage_result_link]: https://sonarcloud.io/dashboard?id=AntaresSimulatorTeam_api-iso-antares

[license_badge]: https://img.shields.io/github/license/AntaresSimulatorTeam/AntaREST

[license_link]: https://www.apache.org/licenses/LICENSE-2.0

[antares-simulator-readthedocs]: https://antares-simulator.readthedocs.io/

[antares-simulator-website]: https://antares-simulator.org

[antares-simulator-github]: https://github.com/AntaresSimulatorTeam/Antares_Simulator
