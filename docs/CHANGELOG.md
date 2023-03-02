Antares Web Changelog
=====================

v2.13.0 (unreleased)
--------------------

### Bug Fixes

*  **ui-map:** prevent duplicate layers and districts on create/update (#1239) ([eff4ca3](https://github.com/AntaresSimulatorTeam/AntaREST/commit/eff4ca369212e9998f9ccd96a938a6f91f5dbf44))
*  **ui-maps:** empty page (#1243) ([71f19d3](https://github.com/AntaresSimulatorTeam/AntaREST/commit/71f19d3484bb802f645140523a7b66f321a2aec2))
*  **api-workers:** prevent scanning of the default workspace (#1244) ([06fd2bc](https://github.com/AntaresSimulatorTeam/AntaREST/commit/06fd2bca478fc4f579ba0760e37969038e560f97))
*  **ui-study:** remove the create command button (#1251) ([463e7a7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/463e7a789eebd2b28c33bd18e833bbd30dc9268a))
*  **ui-wording:** correct wording of user messages (#1271) ([7f66c1a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7f66c1aa518bea09c2db52ae87ef36e14cd5b9e0))
*  **ui-wording:** correct french translations (#1273) ([f4f62f2](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f4f62f252d8b5556ba1cb2b6027360b9066327e0))


### Features

*  **ui-common:** add doc link on subsections (#1241) ([1331232](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1331232e418ebfbf3cc1a82725b95cb11cf8b9bc))
*  **api-websocket:** better handle the events in eventbus braodcasting (#1240) ([99f2590](https://github.com/AntaresSimulatorTeam/AntaREST/commit/99f25906559f782bcad857650f1b8ebfcfe584c8))
*  **ui-commands:** add confirm dialog on delete command (#1258) ([0be70f8](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0be70f87ec03c491faf1d29c8d78b29615d1da9a))
*  **redux:** extend left menu by default (#1266) ([1c042af](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1c042af7d4c713bcbd530062cb9e31ead45e1517))
*  **ui-study:** add text ellipsis on study name (#1270) ([6938114](https://github.com/AntaresSimulatorTeam/AntaREST/commit/69381145ab1e4224e874a59dcec2297dae951b51))
*  **launcher:** integrate Antares Solver v8.5.0. (#1282) ([57bbd3d](https://github.com/AntaresSimulatorTeam/AntaREST/commit/57bbd3d0974b104dc4b58f0f1756e40f50b2189f))
*  **ui:** add tooltips to folded menu (#1279) ([b489dd9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b489dd9db8e5d5b3a8ab6a29721d292d3841dcce))
*  **github:** add feature request template (#1284) ([73aa920](https://github.com/AntaresSimulatorTeam/AntaREST/commit/73aa920fa15d5a3397d49e00319acf808678d021))
*  **github:** add bug report template  (#1283) ([8e05370](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8e05370c5b1ba212545515984eb379c7a7fe6f9d))
*  **ui-results:** add download button on results matrix (#1290) ([343df96](https://github.com/AntaresSimulatorTeam/AntaREST/commit/343df968fec3dc6658f1e41040bc656cd80a104c))
*  **ui-redux:** add menu state in local storage (#1297) ([3160f29](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3160f295ffd06312f2a77ec0ea2dd7da0c04fbed))
*  **ui-study:** add path tooltip on study title (#1300) ([429d288](https://github.com/AntaresSimulatorTeam/AntaREST/commit/429d288ce5aa96c0c65724647b211639b4153417))
*  **ui-map:** add layers and districts French translations (#1292) ([12f4e92](https://github.com/AntaresSimulatorTeam/AntaREST/commit/12f4e9235d5cd2256a52d9e31ec440c0756272b4))


### Code Refactoring

* simplify the maintenance mode and service. ([1590f84](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1590f840dbec5ca4fcd1eba2c125de3e4f40ebef))
* change the `MaintenanceMode` class to implement a conversion from/to `bool`. ([a5a5689](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a5a568984c9562e3eba67ba30c0a076b8f30190e))


### Build System

* update version to 2.13.0 ([a44a896](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a44a8964da226931b7a67b95765abc7baf031eb4))
* remove redundant call to `mypy` in GitHub actions. ([96e2b82](https://github.com/AntaresSimulatorTeam/AntaREST/commit/96e2b824eb348d1a3fe5bacf89de35e9cb7fc0fa))
* upgrade Black version in `requirements-dev.txt` and `.github/workflows/main.yml`. ([464c7ff](https://github.com/AntaresSimulatorTeam/AntaREST/commit/464c7ff1ea877646815a3c70891e36b976b856d8))


### Styles

* fix mypy error: Unused "type: ignore" comment. ([86f9076](https://github.com/AntaresSimulatorTeam/AntaREST/commit/86f90764591e7b863db236891e2aba926d4b1ab1))
* Reformat the source code and unit tests in accordance with the rules of black v23.1.0 (new release). ([73bc5b0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/73bc5b0f7f858f589d525f39228b0af4963dd4be))


### Continuous Integration

* remove Create Issue Branch app file (#1299) ([4e81fa6](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4e81fa646552a58d56984171c644104d4dd79ab7))


### Contributors

<a href="https://github.com/hdinia">hdinia</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/pl-buiquang">pl-buiquang</a>
