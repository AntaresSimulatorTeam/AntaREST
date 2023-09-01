Antares Web Changelog
=====================

v2.14.6 (2023-09-01)
--------------------

> 🚩 NOTE
> 
> From a user perspective, this release does not include any new features or bug fixes.
> 
> This release is solely focused on developers and aims to enhance code quality and readability by organizing imports and extending line width to 120 characters.
> We will now be using [iSort](https://isort.readthedocs.io/en/latest/) for import sorting.
> The configuration for [Black](https://black.readthedocs.io/en/stable/) code formatting has been updated.

### Styles

* add configuration for iSort ([0b20e5d](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0b20e5de8290e59b40edf74f54b16405eeadb30f))
* sort imports in project base code and unit tests using iSort ([ec8b757](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ec8b757f1b89cf80ec9558ca2def52c5bdc9b348))
* ignore unused imports in `dbmodel.py` ([175b7fe](https://github.com/AntaresSimulatorTeam/AntaREST/commit/175b7fe89c6cd96acc89797a447711a61f8b4d3a))
* remove unused imports in production base code ([3d98f93](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3d98f936b20b278bebf9f2ea61223f3aa214ce89))
* remove unused imports in unit tests ([6ea3370](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6ea3370e755a6b2abf7f217662cd89f24ad627f0))
* sort imports in project base code and unit tests using `line_length = 120` ([c0daaf7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c0daaf7fc44b9c53411c9e54986c276c5e8b26f7))
* reindent project base code and unit tests using `line-length = 120` ([2280d27](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2280d276191c0d88eaadacfda2854873d0591f2f))
* reindent `scripts/` directory using `line-length = 120` ([c125fc7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c125fc75caec604809f7ed3414a261547458a633))


### Chore

* increase line length limit to 120 characters for Black and iSort ([f8d45d4](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f8d45d400dcba601a5e8bf360fda60dd0d3d1064))
* remove `# fmt: off`/`# fmt: on` Black directives ([c29dcac](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c29dcac2d1eedd547a2c6cef50b41c6ec0816046))


### Build System

* add iSort in the `requirements-dev.txt` ([b3ff6b9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b3ff6b9f84642d5927c8ec715356f52bfda25a74))


### Continuous Integration

* change the main GitHub action to run iSort for code style checking ([b2efeab](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b2efeab51586fffdbb4fc28c6d555004759e6e3e))
* correct the main GitHub action to use `Black~=23.7.0` ([c72d0d5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c72d0d5d25984cd0b9a1bef90c58c1db698438b5))


### Code Refactoring

* fix lambda capturing `name` variable reported by SonarCloud ([42d2213](https://github.com/AntaresSimulatorTeam/AntaREST/commit/42d2213e4682e35da40931cd50190f368ecac951))
* correct SonarCloud issues ([693ae07](https://github.com/AntaresSimulatorTeam/AntaREST/commit/693ae07c122e8bdf81932a7fc618e80c1fa9aa45))
* avoid always returning the same value (reported by SonarCloud) ([314da0b](https://github.com/AntaresSimulatorTeam/AntaREST/commit/314da0b3d9151a0c5cdd8d27f3e52af2732b389e))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>


v2.14.5 (2023-08-11)
--------------------

### Features

*  **ui-i18n:** add missing adequacy patch translations (#1680) ([8a06461](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8a06461f4118227b94be7f587d37ea2430c70505))
*  **ui:** removed the "patch" number from the list of versions in the simulation launch dialog when it's equal to 0 (#1698) ([1bc0156](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1bc0156c3e08e321e9ccc396b95cadeabf1c1fc7))


### Bug Fixes

*  **web:** modified API response model to prevent Watcher's ValidationError (#1526) ([b0e48d1](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b0e48d1bd31463cb6ce5e9aefeff761c016d0b35))
*  **xpansion:** corrected field types for Xpansion parameters (sensitivity analysis) ([3e481b9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3e481b9c8866ecc3dc42e351552e1ded036f62ad))
*  **variant:** fixed implementation of the method for extracting the difference between two studies ([c534785](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c5347851da867a19b990e05c6516bedc7508c8ce))
*  **api:** added missing `use_leeway` field and validation rules in the hydro configuration form (#1650) ([27e46e5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/27e46e5bda77aed65c84e82931d426b4b69a43bd))
*  **export:** ZIP outputs are no longer compressed before export (used by Xpansion) (#1656) ([cba6261](https://github.com/AntaresSimulatorTeam/AntaREST/commit/cba62613e19712240f74f417854e95bd588ba95d))
*  **log-parser:** simplified analysis and improved accuracy in displaying simulation progress for a study (#1682) ([2442674](https://github.com/AntaresSimulatorTeam/AntaREST/commit/24426749e9b6100eb3ab4b7159f615444242b95a))
*  **table-mode:** corrected reading of UI information when the study has only one area (#1674) ([55c4181](https://github.com/AntaresSimulatorTeam/AntaREST/commit/55c4181b64959c5e191fed2256437fc95787199f))
*  **table-mode:** issue to read area information in the case where the study has only one area (#1690) ([87d9617](https://github.com/AntaresSimulatorTeam/AntaREST/commit/87d961703cebdc037671fe73988903eb14dd9547))
*  **command:** improve INI reader to support API PUT `/v1/studies/{uuid}/raw` (#1461) ([9e5cf25](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9e5cf25b2f69890016ea36f3be0e9ac03c7695b6))
*  **variant:** fixed time series deletion of renewable clusters (#1693) ([4ba1b17](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4ba1b17dd3c1b8ea62a5a02f39d15e94a4b9a331))
*  **launcher:** fixing launcher versions display and creation of the endpoint `/v1/launcher/versions` ([410afc2](https://github.com/AntaresSimulatorTeam/AntaREST/commit/410afc2e4ecbb296878985839ee27f84bc70d9d8))
   and (#1672) ([a76f3a9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a76f3a9f01df0225d7fb54b20ba3ff599d749138))
*  **launcher:** set the default number of cores to 22 (instead of 12) (#1695) ([2c89799](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2c8979916d46a0ed46a67bc75ac9a2e365e3f164))


### Continuous Integration

* upgrade mypy to v1.4.1 and Black to v23.7.0 for improved typing and formatting (#1685) ([7cff8c5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7cff8c56c38728a1b29eae0221bcc8226e9ca80c))


### Tests

* enhanced integration tests: refactored fixtures and resources ([70af9b1](https://github.com/AntaresSimulatorTeam/AntaREST/commit/70af9b167bf54d534696da8b781edda56ccee788))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>,
<a href="https://github.com/hdinia">hdinia</a>,
<a href="https://github.com/skamril">skamril</a>


v2.14.4 (2023-06-28)
--------------------

### Bug Fixes

*  **launcher:** take into account the `nb_cpu` in the local Solver command line (#1603) ([7bb4f0c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7bb4f0c45db8ddbaedc1a814d0bfddb9fb440aba))
*  **api:** resolve version display issue in Desktop's `/version` endpoint (#1605) ([a0bf966](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a0bf966dc0b7a0ee302b7d25ff0d95f5307d8117))
*  **study:** fixing case sensitivity issues in reading study configuration (#1610) ([f03ad59](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f03ad59f41a4d5a29a088e7ff98d20037540563b))
*  **api:** correct `/kill` end-point implementation to work with PyInstaller ([213fb88](https://github.com/AntaresSimulatorTeam/AntaREST/commit/213fb885b05490afe573938ec4300f07b561b2dd))
*  **fastapi:** correct URL inconsistency between the webapp and the API (#1612) ([195d22c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/195d22c7005e2abad7f389164b0701a8fa24b98c))
*  **i18n:** wrong translations and add missing keys (#1615) ([7a7019c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7a7019cc1e900feaa5681d2244a81550510e9a78))
*  **deploy:** change example study settings to allow parallel run (#1617) ([389793e](https://github.com/AntaresSimulatorTeam/AntaREST/commit/389793e08dee0f05dfe68d952e9b85b64b3bc57e))
*  **variant:** get synthesis now also works for level 2+ variants (#1622) ([661b856](https://github.com/AntaresSimulatorTeam/AntaREST/commit/661b856331673ac792fd2ca264d0fb45433d3ee5))
*  **results:** refresh study outputs when job completed and add back button (#1621) ([39846c0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/39846c07db0ccd540fcf73fe8a5d711012101226))
*  **deploy:** remove unnecessary Outputs from "000 Free Data Sample" study (#1628) ([a154dac](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a154dacdc11e99a38cbc2d2930c50875563b76a2))


### Documentation

*  **model:** add documentation to the `Matrix` and `MatrixDataSet` classes ([f7ae5f4](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f7ae5f4735eb4add02c8aa951eaf30405748dfe6))


### Code Refactoring

*  **api:** remove unused protected function ([6ea3ad7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6ea3ad7208fd16746bd134aebf8ed8ea9b3da61d))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>,
<a href="https://github.com/skamril">skamril</a>


v2.14.3 (2023-06-20)
--------------------

### Bug Fixes

*  **desktop:** correct Antares Desktop packaging ([95d7544](https://github.com/AntaresSimulatorTeam/AntaREST/commit/95d754473d63596fd6844cfb97d47a3f2041e2ba))
*  **error:** improve error handling with enhanced error message (#1590) ([9e22aee](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9e22aee25a812b81a323c83a043ffc36f0b1eb46))
*  **matrix:** significant performance enhancement for Time Series update (#1588) ([220107a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/220107aa2ff18be556960ecf367816cd1aa4ed3f))
*  **launcher:** correct the launching of the local Antares Solver ([8a31514](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8a31514f5995d02e7e23402251396bda2ce22580))
*  **api:** add missing "annual" key on correlation config for new areas (#1600) ([ac98a76](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ac98a76ca591dc1d582eacd5d00c258bbf06ac5f))


### Documentation

* update user instructions for Antares Web Desktop version ([98bcac5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/98bcac590ba21cae68980172f120627143f090d4))


### Features

*  **common:** display a snackbar error when async default values failed in Form (#1592) ([c213437](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c213437fc4ac82ac5c1aab4dcdf6638729b81497))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/hdinia">hdinia</a>


v2.14.2 (2023-06-12)
--------------------

### Bug Fixes

*  **renewable:** fixing issue with missing display of renewable cluster form (#1545) ([03c7628](https://github.com/AntaresSimulatorTeam/AntaREST/commit/03c76280a88373ace47121bd44a2fe529bcd7343))
*  **worker:** archive worker must be kept alive for processing (#1567) ([34e1675](https://github.com/AntaresSimulatorTeam/AntaREST/commit/34e1675737d5af390f4be97b47898ad1e60a7b51))
*  **build:** fix pyinstaller build (#1566) ([2c7b899](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2c7b89936afb0ebc03d79f9505daa901c1a8a003))
*  **desktop:** correct date parsing in localized environment (#1568) ([1d9177a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1d9177af66e68983a8db3ca3858449605b24d9f9))
*  **matrix:** check invalid params and empty matrix in matrix update (#1572) ([f80aa6b](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f80aa6b2178192660d55370977f1495ed1e72f00))
*  **model:** raise an error if the "about-the-study/parameters.ini" file is missing in the ZIP file (#1582) ([c04d467](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c04d4676aaa7319e308d36d2345fb76d59d3119b))


### Features

*  **matrix:** improve matrix read/write using NumPy (#1562) ([2784828](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2784828b7f10ff53d2f59ca594525243d97aaa6a))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>


v2.14.1 (2023-05-15)
--------------------

### Bug Fixes

*  **storage:** performs a partial unzip to read the config of the simulation results ([61e019d2](https://github.com/AntaresSimulatorTeam/AntaREST/commit/61e019d27d5015ba009f527381dab59ce330ce0e))


v2.14.0 (2023-05-12)
--------------------

### Features

*  **api-hydro:** add allocation form endpoints ([b2bee0e](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b2bee0ed8e9817da2ed642474504fb25a95a8360))
*  **api:** update optimization form endpoint and add adequacy patch form endpoint ([dfa1b27](https://github.com/AntaresSimulatorTeam/AntaREST/commit/dfa1b2729ddb3e46f3b7f65a4a0079211da2c69c))
*  **ui-config:** update optimization form and add adequacy patch form ([f68c54b](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f68c54b9b846d32e65d32c14c8931c625a6bd498))
*  **ui-hydro:** add allocation form ([5dbb85f](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5dbb85fdc733731c5fc16a258666869486b5cddf))
*  **ui-hydro:** add inflows structure tab ([a466e34](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a466e3459e25ece8f2d80c8eb501ba05c717d5fa))
*  **ui-hydro:** add row names ([94dc38c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/94dc38c1fe2f5163f6b44dc31cc3639e63cd2131))
*  **ui-hydro:** display area name instead of ID ([0df0b21](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0df0b2121e761a91946452874d70bc80dbe07647))
*  **ui-hydro:** update allocation form styles ([ac470c1](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ac470c19410bf2d13b57ecc0bab650b24b77c495))
*  **ui-matrix:** update "Time" column and add index row headers ([3d50bf9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3d50bf9617367fe8d1fcd21e6a9835834456a10f))
*  **ui:** add @total-typescript/ts-reset lib and tsUtils (#1408) ([aa5e3e8](https://github.com/AntaresSimulatorTeam/AntaREST/commit/aa5e3e87d95b8b5061030025e89443e1fc71823d))
*  **ui:** update react-hook-form lib and use the new API (#1444) ([1d129d9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1d129d9d6bac97deee9ebc98d3334117fe837444))


### Bug Fixes

*  **common:** field array change doesn't trigger on auto submit (#1439) ([910db64](https://github.com/AntaresSimulatorTeam/AntaREST/commit/910db64ca872468a1f01ced99083962022daa05c))
*  **matrix:** correct the frequency of some matrices (#1384) ([2644416](https://github.com/AntaresSimulatorTeam/AntaREST/commit/26444169b9ab60f54e8ee7a2d16fb10dbc4d537e))
*  **ui-common:** add matrices float handling ([99ba81f](https://github.com/AntaresSimulatorTeam/AntaREST/commit/99ba81fce26bbd99340990d0207761463558d4a7))
*  **ui-hydro:** correct column names ([e529a79](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e529a799071e9c5485e2cba35eb5a7c2c18c25e7))
*  **ui-hydro:** update hydro matrices columns ([56641d7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/56641d7ad995d8b7dd6755b13f1689b32b6296d8))
*  **ui:** fix typo on error page (#1390) ([da00131](https://github.com/AntaresSimulatorTeam/AntaREST/commit/da0013190d7e31e1afe9d8f5c3b03c378ca41507))
*  **ui:** size issue with HandsonTable ([f63edda](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f63edda65345bf9848fb44a8a067a885ca5fbd83))


### Styles

*  **api-tablemode:** fix typo ([5e5e4e7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5e5e4e7efcfc93e4682825a9c514417679fba89b))
*  **ui:** fix filename ([ad9f9c0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ad9f9c055713ef81a94b8c7bb01caae783ab8de9))


### Documentation

*  **api:** add API documentation for the hydraulic allocation (and fix minor awkwardness) ([08680af](https://github.com/AntaresSimulatorTeam/AntaREST/commit/08680af4344b7dd9aa365267a0deb8d9094f0294))
*  **study-upgrade:** add the "How to upgrade a study?" topic in the documentation (#1400) ([2d03bef](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2d03befe999e558c989e1cce1f51186beff5502b))

> IMPORTANT: The `antares-launcher` Git submodule is dropped.


### Contributors

<a href="https://github.com/hdinia">hdinia</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/flomnes">flomnes</a>,
<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>


v2.13.2 (2023-04-25)
--------------------

### Bug Fixes

*  **api:** fix uncaught exceptions stopping slurm launcher loop (#1477) ([2737914](https://github.com/AntaresSimulatorTeam/AntaREST/commit/27379146cfa12cc90e38f2f0d77009d80f3164db))

### Contributors

<a href="https://github.com/sylvlecl">Sylvain LECLERC</a>

v2.13.1 (2023-04-11)
--------------------

### Bug Fixes

*  **desktop:** use Antares Solver v8.5 for Antares Web Desktop version (#1414) ([6979e87](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6979e871dac39a34e76fe6a72b2ccf4502e8a288))
*  **launcher:** improved reliability of task state retrieval sent to SLUM (#1417) ([101dd8c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/101dd8c2a149c5112669d557d0851a9b1659d683))
*  **api:** show Antares Launcher version in the `/version` end point (#1415) ([12bfa84](https://github.com/AntaresSimulatorTeam/AntaREST/commit/12bfa849e2232ea275851ad11407faf70bb91d2c))
*  **desktop:** use Antares Solver v8.5.0 for Antares Web Desktop version (#1419) ([8f55667](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8f55667b52eea39a7d0e646811f16ef024afbbe0))
*  **api:** better handling of exception to catch the stacktrace (#1422) ([a2d0de0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a2d0de073582070282131b3bcd346e6fbe7315ab))


### Contributors

<a href="https://github.com/laurent-laporte-pro">Laurent LAPORTE</a>, and
<a href="https://github.com/MartinBelthle">MartinBelthle</a>


v2.13.0 (2023-03-09)
--------------------

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


### Bug Fixes

*  **api-workers:** Prevent scanning of the default workspace (#1244) ([06fd2bc](https://github.com/AntaresSimulatorTeam/AntaREST/commit/06fd2bca478fc4f579ba0760e37969038e560f97))
*  **ui-study:** remove the create command button (#1251) ([463e7a7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/463e7a789eebd2b28c33bd18e833bbd30dc9268a))
*  **ui-wording:** correct wording of user messages (#1271) ([7f66c1a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7f66c1aa518bea09c2db52ae87ef36e14cd5b9e0))
*  **ui-wording:** correct french translations (#1273) ([f4f62f2](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f4f62f252d8b5556ba1cb2b6027360b9066327e0))
*  **api:** correct the way the task completion is notified to the event bus (#1301) ([b9cea1e](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b9cea1ebd644869a459cbf002661c4a833389cb2))
*  **storage:** ignore zipped output if an unzipped version exists (#1269) ([032b581](https://github.com/AntaresSimulatorTeam/AntaREST/commit/032b58134a4e2e9da50848d6de438d23a0f00086))


### Build System

* update version to 2.13.0 ([a44a896](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a44a8964da226931b7a67b95765abc7baf031eb4))
* remove redundant call to `mypy` in GitHub actions. ([96e2b82](https://github.com/AntaresSimulatorTeam/AntaREST/commit/96e2b824eb348d1a3fe5bacf89de35e9cb7fc0fa))
* upgrade Black version in `requirements-dev.txt` and `.github/workflows/main.yml`. ([464c7ff](https://github.com/AntaresSimulatorTeam/AntaREST/commit/464c7ff1ea877646815a3c70891e36b976b856d8))

> IMPORTANT: The `antares-launcher` project (source files) is no longer needed,
> because the `Antares-Launcher` Python library is now declared as a dependency
> in the `requirements.txt` file.


### Styles

* fix mypy error: Unused "type: ignore" comment. ([86f9076](https://github.com/AntaresSimulatorTeam/AntaREST/commit/86f90764591e7b863db236891e2aba926d4b1ab1))
* Reformat the source code and unit tests in accordance with the rules of black v23.1.0 (new release). ([73bc5b0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/73bc5b0f7f858f589d525f39228b0af4963dd4be))


### Continuous Integration

* remove Create Issue Branch app file (#1299) ([4e81fa6](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4e81fa646552a58d56984171c644104d4dd79ab7))


### Contributors

<a href="https://github.com/hdinia">hdinia</a>,
<a href="https://github.com/laurent-laporte-pro">Laurent LAPORTE</a>,
<a href="https://github.com/pl-buiquang">pl-buiquang</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>
