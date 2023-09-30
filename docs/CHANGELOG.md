Antares Web Changelog
=====================

v2.15.0 (2023-09-30)
--------------------

### Features

* **antares-launcher:** use antares launcher v1.3.1 [`#1743`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1743)
* **api:** add Properties form endpoint [`31898a1`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/31898a1306d7a2115de20ca0226f8fc436377588)
* **api:** add api doc and integration test [`51db54f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/51db54fec714cf9aac30ce1f7543e58b5ab1ff6e)
* **api:** add new pollutants in thermal manager [`bcd5a01`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/bcd5a01e6878048512550d26834d4dad335b975e)
* **api:** change the response model of "launcher/_versions" endpoint to return a list of versions [`e7089a1`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e7089a1a5407640fa49f0230c812257f5ac7cecf)
* **api:** correct default values for "/launcher/versions" endpoint [`f87ccca`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f87ccca0c1b6c41fb9e0cb6e0e7435b4df59500f)
* **api:** improve error handling in "launcher/_versions" endpoint [`f84ff84`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f84ff849b0ab69a0a0e4344cfd408880e843b0e9)
* **api:** improve exception handling in "launcher/_versions" endpoint [`1263181`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/12631818a1d515485af2827c76acf2b91ad66245)
* **api:** improves "launcher/_versions" endppoint [`ae6c7d6`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ae6c7d6cb1b4d3de2a96b3ed9f7b46db712eae6d)
* **api:** replace "launcher/_versions" endpoint by "/launcher/versions" [`fb294dd`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/fb294dd81e520834998883deb1d3561c07484b60)
* **api-layers:** minor improvements [`ef7e21f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ef7e21fc612acf53e642b7bbc334baedf52e952c)
* **business:** add xpansion batch size back office [`#1485`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1485)
* **commands:** add ST-Storage commands [`#1630`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1630)
* **common:** add undo/redo to Form component [`fc02c00`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/fc02c00aea2c9b7d6cd9464346e8962d5304ca1c)
* **common:** multiple updates on Form component [`2193e43`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2193e431d67d0f1807a2d1cc0853329871c63479)
* **matrix:** improve matrix read/write using NumPy [`#1452`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1452)
* **matrix:** improve matrix service read/write using NumPy [`8c2f14f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8c2f14fa027ac5e0ceba9a5c027fd409feff49ce)
* **matrix:** improve unexpected exception error message [`#1635`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1635)
* **matrix-service:**  improve the importation function to handle NumPy arrays directly without the necessity of converting them [`ecf971a`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ecf971a142533f6c8d4103cd554ebd8278b86227)
* **matrix-service:** avoid having to save the matrix again [`a40ad09`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a40ad09a61fe5292ec2cfca08cea383868006e54)
* **matrix-service:** enhance the `ISimpleMatrixService` class and sub-classes to support creating from NumPy array [`93737ae`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/93737aecc130f991e8cebfb5d042eab031c18046)
* **matrix-service:** enhance the `MatrixContentRepository` class to support saving NumPy array directly [`1bf113b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1bf113bec8fbd6aa868752342d3727b2c2a8792f)
* **matrix-service:** ensure exclusive access to the matrix file between multiple processes (or threads) [`66ce1bc`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/66ce1bc42f7512469352e899b4dce25289790a52)
* **model:** handle 8.6 study model and study upgrader [`#1489`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1489)
* **service:** assign to a copied study all groups of the user [`#1721`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1721)
* **service:** set `PublicMode.READ` when importing is done by user with no groups [`#1649`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1649)
* **service:** set `PublicMode` to `READ` when importing is done by user with no groups [`04d70ed`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/04d70ed6be492fc860701273cce36b631798c568)
* **service:** set the user's name as author in `study.antares` when creating a study [`#1632`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1632)
* **st-storage:** add ST Storage API endpoints [`#1697`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1697)
* **storage:** ini reader can now take ioTextWrapper as input [`015bc12`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/015bc12a5e1530144133cb072633a8ec4f2e3e23)
* **style:** code style and refactoring enhancements [`8b4ec2e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8b4ec2e4f5264a87da78a41443b28daef6303d00)
* **ui:** add and use correct launcher verisons instead of study's [`1878617`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1878617c2911f653f72bd8f13d9180cac225f42e)
* **ui:** enable undo/redo on some forms [`d0d07e9`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d0d07e92b17151ef1c650b5cb6b12b67f3b6e6e3)
* **ui-common:** add GroupedDataTable [`#1633`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1633)
* **ui-common:** add submitButtonIcon prop in Form [`6b16e01`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6b16e010f143b859d6214d2f7cd850e7b72f44ec)
* **ui-common:** display submit error in Form [`92d5a1e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/92d5a1ed3c2c98802e3a65f49985960183bb6ac5)
* **ui-common:** increase the width of the first column on tables [`d3d70ff`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d3d70ff6d1e271378cc360cd28953bdb42e90c98)
* **ui-common:** update ColorPickerFE [`8347556`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8347556d947dc5c005492421cc4722c360ce0373)
* **ui-config:** enable undo/redo in adequacy patch form [`#1543`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1543)
* **ui-i18n:** add missing adequacy patch translations [`#1680`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1680)
* **ui-lib:** add material-react-table package [`e88fb69`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e88fb69b30c319f27a37b3c298a8aaff6bd98f34)
* **ui-login:** update form [`9631045`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9631045d9f40446264dcad896e5672f3aff4a77d)
* **ui-map:** add map zoom buttons [`#1518`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1518)
* **ui-study:** enhance study upgrade dialog [`#1687`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1687)
* **ui-thermal:** add new pollutants [`5164a4c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5164a4cb5a894f5b96f6c0fd21b358e4df072aec)


### Bug Fixes

* **api:** Correct endpoint for `HTTPStatus.NO_CONTENT` (204) [`b70bc97`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b70bc977f2a3245944f54d19ebb6e792345b03df)
* **api:** add missing `use_leeway` field and validation rules [`#1650`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1650)
* **api:** correct API endpoints and CLI tools [`#1726`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1726)
* **api:** correct `update_area_ui` endpoint response model [`963f5ee`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/963f5ee84fa7409a8fcf4effa88007362305d6ab)
* **api:** correct exception handling in `extract_file_to_tmp_dir` [`af38216`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/af38216e685b9f9d37e14cb66aa1300fe1cc592c)
* **api:** correct response model of "/studies/_versions" endpoint [`91da3e7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/91da3e775086d4f19207bce2d2f684729b694c0d)
* **api:** correct the regex in `IniReader` to match a section in square brackets [`123d716`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/123d716c68584c8c2ce5d907991c7379e21f0a4a)
* **api:** enhance Python detection in version info endpoint [`86fb0e5`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/86fb0e5baa59e1508e239d195894ab186b47189d)
* **api:** sanitize and avoid duplicates in group IDs lists [`8c9ac99`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8c9ac998fbd4610ca8c7de338adeff53ca08b2cd)
* **api:** standardize 'areas_ui' to dict format for single area case [`#1557`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1557)
* **api:** study data retrieval now considers document types, enabling retrieval of Microsoft Office documents. Binary data support has also been enhanced [`8204d45`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8204d45867f54337306d463e217ae259b3cc761f)
* **api,tablemode:** wrong adequacy patch mode path and clean code [`0d00432`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0d00432910cbd6c761a17e69571ef46ec1839dc2)
* **api-layers:** fixed issue preventing layers deletion when no areas [`b3f98f2`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b3f98f2c12b0042d35f9421388b5f33858f18189)
* **api-layers:** remove unnecessary parameter that causes tests to fail [`052a9f3`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/052a9f38ea5c96d0aac0a0f050cabbe21153a761)
* **build:** fix pyinstaller build  [`#1551`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1551)
* **command:** change code according to comments [`f3c68d2`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f3c68d2d8cf323a36582a5e5a165c1ddf23c0d7c)
* **command:** fix update_config to support API PUT v1/studies/{uuid}/raw [`ffed124`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ffed124cb17965e41409812a83da2bf36da8b014)
* **docs:** update README, removing obsolete instructions [`#1552`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1552)
* **export:** ZIP outputs are now uncompressed before export [`#1656`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1656)
* **filesystem:** correct the handling of default matrices in `InputSeriesMatrix` node [`#1608`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1608)
* **launcher:** fixing launcher versions display and API endpoint for solver versions [`#1671`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1671)
* **log-parser:** simplify parsing and make it accurate [`#1682`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1682)
* **matrix:** correct the loading and saving of empty matrices as TSV files [`#1746`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1746)
* **matrix:** create empty file if the matrix is empty [`9155566`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9155566ec6b2d52c97c4d9fc5bbefbada20a91bf)
* **matrix-service:** correct the `MatrixService.create` so that the matrix file is not deleted in case of exception [`1860379`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1860379a96cd7ab87c150788c5d2efedd91d5859)
* **matrix-service:** prevent the use of scientific notation when saving matrices [`7387248`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/73872489fb57560e74172b4d5dfc9532ce6660bb)
* **model:** wrong frequency for `hydro energy credits` matrices [`#1708`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1708)
* **packaging:** update the packaging script to use Antares Solver v8.6.1 [`#1652`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1652)
* **service:** set public mode to `NONE` and assign user groups to the study during copying [`#1620`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1620)
* **service:** set public mode to `NONE` and assign user groups to the study during import [`#1619`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1619)
* **st-storage:** add default value for st storage group [`f9a3af7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f9a3af75bc564e75296de35814ee4d625d822c84)
* **st-storage:** allow DELETE endpoint to accept multiple IDs as parameters [`#1716`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1716)
* **st-storage:** correct docstring [`60bdbbf`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/60bdbbfe805bff8df7a6619b0b3227b14e0d4ed5)
* **st-storage:** fixing archived study configuration reading for short-term storages [`#1673`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1673)
* **st-storage:** parse_st_storage works with zipped study with version previous 860 [`0cae9f2`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0cae9f2e535b29e11b1ef62234dd3ef4f1afcbfe)
* **st-storage:** replace inflow.txt by inflows.txt according to the changing doc [`#1618`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1618)
* **st-storage:** update "group" parameter values for Short-Term Storage [`#1665`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1665)
* **storage:** fix INI file writing anomaly in Antares study update [`#1542`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1542)
* **table-mode:** fixes the reading of UI information in the case where the study has only one area  [`#1674`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1674)
* **table-mode:** issue to read area information in the case where the study has only one area [`#1690`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1690)
* **tests:** use deepcopy for dict to only modify the copy [`bca0d60`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/bca0d6062f9fef7d672a4059163e14d21d4624fe)
* **thematic-trimming:** correct the name of the "Profit by plant" variable [`7190ee1`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7190ee12fc16ea9617888574fa20e86306fa421d)
* **ui-api:** resolve Area deletion & Layers/Districts UI modification issues [`#1677`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1677)
* **ui-common:** error with formState in Form [`121d4e5`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/121d4e5343a87f15f34a1a63108d6888232ffef4)
* **ui-common:** prevent null values for string cells in HandsonTable component [`#1689`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1689)
* **ui-debug**: issue to display json file in outputs [`#1747`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1747)
* **ui-i18n:** add missing key [`685c487`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/685c487f0f73d8eb37b1594c5e46b283dd55d8d4)
* **ui-i18n:** missing key [`7c8de2a`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7c8de2a883e646d927b52e28baa0184a13146625)
* **ui-map:** area persistence issue after deletion [`47d6bb6`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/47d6bb666aa3d98ff98724fccd6b8504f9d27d29)
* **ui-model:** update Properties form with the new endpoint [`15d5964`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/15d596494827e3f14eaf77d65e0a8c6db411802b)
* **ui-redux:** missing state update for layers/districts after node deletion [`42d698c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/42d698cf89a8eec41475c7f3640e0d29b69bba14)
* **ui-redux:** remove eslint no-param-reassign warning [`3f88166`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3f88166c18337f2a4bf096d1a28664d793198d46)
* **ui-xpansion:** add the missing `batch_size` field in the Xpansion parameters view [`#1739`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1739)
* **variant:** enhance `VariantCommandsExtractor` for Renewable Clusters and Short-Term Storage [`#1688`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1688)
* **variant:** fixed TS deletion of renewable clusters and short-term storage [`#1693`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1693)
* **variant-manager:** correct the variant manager [`5cc467f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5cc467f48a2f6b73d9abf652391c14bef76d40fc)
* **web:** change API response_model to avoid ValidationError [`#1526`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1526)
* **worker:** archive worker must be kept alive for processing [`#1558`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1558)
* **xpansion:** correct field names and types in Xpansion settings [`#1684`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1684)
* correct the import of `declarative_base` to avoid a deprecation warning. [`c8c8388`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c8c8388e5db898da897f28f5a4cd76c3485571da)


### Documentation

* **api:** improve the documentation of the study upgrade and import endpoints [`a8691bb`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a8691bb7963fc5d9cfa6e06175f4827e455eee44)
* correct and improve the "Variant Manager" documentation [`#1637`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1637)
* update changelog for the v2.15 release [`ccd6496`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ccd6496266dea01ff952c41565d8940391f0f317)


### Tests

* **api:** correct JSON payloads for "table mode" [`41b2cc8`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/41b2cc8a58373c41e54c452d2667206680d39fb8)
* **api:** correct unit tests for Xpansion-related endpoints to use bytes for file upload [`7936312`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7936312c1caa178e59f79b6cf8516a4c6bea855e)
* **api:** improve unit test of `get_dependencies` endpoint [`0524e91`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0524e91d343b9a73414110c25094064342d25a77)
* **api:** simplify initialization of the database in unit tests [`#1540`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1540)
* **api:** update `UploadFile` object construction for `Starlette` &gt;= 0.24 [`d9c5152`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d9c5152110420a10a4e73de7db6d6316c6a707f6)
* **api:** update integration tests for Starlette 0.21.0 [`ec3c7b7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ec3c7b76f82c612fb40937dddce14207735be38f)
* **api:** update stream file download tests for compatibility with Requests and Httpx [`ce6bdc5`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ce6bdc539a1ba8ae1d4d81342e90e5369706f426)
* **api-layers:** add layers management tests [`4523022`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4523022d7f7df8a5b2a35f8aba1687de3c854427)
* **export:** correct unit tests for `VariantStudyService.generate_task` method [`f533fdc`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f533fdc6776bc2b4201023df391e8054b1f406b2)
* **ini:** correct the `IniFileNode` unit tests [`b96a92e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b96a92eadb6ca8b69b1bfc2e335a5535d67f52b1)
* **matrix:** use NumPy arrays in `parse_commands` UT and correct path on Windows [`2528cce`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2528cce0226096f717df432f2a6b56248da57330)
* **matrix-service:** improve unit tests for `MatrixContentRepository` class [`e35639f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e35639f5d26d93e3619c3ff6335db33d6f8e9b56)
* **matrix-service:** improve unit tests for `MatrixService` class [`8cf9f94`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8cf9f94e8e5b79a966552e9728d50455b885b117)
* **st-storage:** improve unit tests to check "group" default value and add typing [`a3051ac`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a3051ac581df99f366ec6ff9595015cecdeec1d8)
* **thematic-trimming:** correct unit test (`study.version` was not set) [`28720f5`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/28720f5d86fad43e3359beb7bdfdbc6c386c7619)
* add Properties form test and fix others one [`5267276`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5267276ce6ea59a36680d242fd939bd295b6a7b6)
* improve and correct unit tests for `AreaManager` [`e6f7ed2`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e6f7ed2e22a51356c039ff3dda42ea33439b9c48)
* improve fixtures in unit tests for better reuse [`#1638`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1638)


### Refactoring

* **allocation:** remove deprecated class `FixedAllocationKeyIniReader` [`b1299fe`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b1299fea4149a57a56bf4e1e002597d7f35a7625)
* **api:** refactor data extraction logic in `_extract_data_from_file` function [`219990b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/219990b14d3a4c9f64189fb7c9d245e9c0afba9c)
* **api-model:** improve `transform_name_to_id` implementation and add UT [`24b1059`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/24b10595cdf7c054815834181a82d65f653f0270)
* **api-model:** improve `transform_name_to_id` implementation for more efficiency [`#1546`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1546)
* **command:** improve implementation of area management [`#1636`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1636)
* **command:** rename "cluster" as "thermal cluster" [`#1639`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1639)
* **matrix:** improve implementation of dataframe saving [`c156c3b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c156c3bc8b312a0932b2b25dc5c835b8e12d2cfc)
* **matrix-service:** improve implementation of `create_by_importation` [`b054b8b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b054b8b72d49966ed46f2110f2a24aedb4549d2b)
* **matrix-service:** simplify timestamp calculation used during `MatrixDTO` creation [`be5aafe`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/be5aafe2fb64bdae2f58c67fa7f69df26277f18d)
* **matrix-service:** use `matrix_id` in favor of `matrix_hash` as matrix hashing is an implementation detail [`fc9e48c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/fc9e48ca7e05c40a25d95c4dd9cd093dc8beb7a3)
* **rawstudy-filesystem:** improve error message raised by `ChildNotFoundError` [`9a6c4f9`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9a6c4f92b704219836e42b15c196f4c317ee3fad)
* **tools:** correct migration from `Requests` to `httpx` [`09be12a`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/09be12a3989dab5a4cdaa6d73f8e77d2e89c521f)
* **tools:** prepare for migration from `Requests` to `httpx` [`f494188`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f494188b97dfa34c0981875d647ac700c44a02f3)
* **variant:** enhance implementation of variant commands [`#1539`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1539)
* avoid always returning the same value (reported by SonarCloud) [`6e4d8cb`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6e4d8cb2f2cc532fe5a48f97e8b94d2df7f1f37a)
* correct SonarCloud issues [`39f584d`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/39f584d1733ebfd3dc9b438a4a6819990c4007ec)
* enhance code quality in variant commands implementation [`608f0b3`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/608f0b38ce92b8186678ab39d8e0a6364d97a7de)
* fix lambda capturing `name` variable reported by SonarCloud [`cb3022c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/cb3022cd5bdd7a3e4b550e028669feba49dd4618)
* refactoring of unit tests and Model improvement [`#1647`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1647)


### Styles

* **api:** change field version check [`d99be3f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d99be3f272fe879edf650e987850d9a4864579b1)
* **matrix-service:** correct the Google docstring format [`26bfc2d`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/26bfc2d02026590c1b30e4adaf119aeaf7ec8c27)
* **ui:** correct spelling mistake in webapp code [`#1570`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1570)
* **ui-redux-map:** minor improvements [`27cb4be`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/27cb4befffab872a403c5ca5b9f15c95a250ac61)
* add configuration for iSort [`cd6ae15`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/cd6ae1591d4026b9b5bf9159c31737ed0b1d0c18)
* correct mypy issues [`8f5f97b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8f5f97b18298c27818b903c8f3475452dfdf5ad3)
* ignore unused imports in `dbmodel.py` [`853af50`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/853af500b7c246cf1f6a32222d71c0c8a45a62b7)
* reindent `ini_reader.py` [`d5fa83d`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d5fa83d7371b533a0b6aac38aac924c3e3d8a0de)
* reindent project base code, `scripts/` and unit tests using `line-length = 120` [`51a0f27`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/51a0f27cebd1216668f3da91b43cd1903b07cbca)
* reindent source code in unit tests [`4515451`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4515451313b5ab3935dfbb360eedce794bfe5d3e)
* remove unused imports in production base code [`9dc34ce`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9dc34cec9f8e719477049a751f2a0d3fa49c9889)
* remove unused imports in unit tests [`496f164`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/496f1640fccf09c63242985f8d41aceba7f78f05)
* sort imports in project base code and unit tests using `line_length = 120` [`13a5929`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/13a59293dba60e709c995cffa15cd27cd830bc35)
* sort imports in project base code and unit tests using iSort [`44ac3d8`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/44ac3d81e8beefe570d536478393c315c7e8d5fa)


### Build System

* **launcher:** use Antares-Launcher v1.3.0 which preserve the "output" directory required by the `--step=sensitivity` Xpansion option [`#1606`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1606)
* add iSort in the `requirements-dev.txt` [`e86b58f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e86b58fe84360ce37786aace48aa0a32f01f8859)
* include `typing_extensions` in the project requirements (new direct usage) [`00ae992`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/00ae9923abcb83e5764eaa09a56fdceb3cc6cfde)
* move `checksumdir` and `locust` libraries from project requirements to tests requirements (only used in unit tests) [`f8d036e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f8d036e021c534eaeed4885397073e1f6e3b9d53)
* remove unused Sphinx-related libraries from docs requirements [`6c3f4bf`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6c3f4bff861ab4f5af36eb3c22dcbf33032a91ee)
* remove unused libraries from project requirements [`c4495a0`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c4495a07db92d90cc38b26ebad5973742713fe3f)
* specify the node versions supported  [`#1553`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1553)
* update project configuration, specify exclusion of non-package directories when using `find_packages` [`236a2d7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/236a2d712858ee23abb7710ef7f92e19042d48cb)
* update project's metadata in `setup.py` (author, author email, license, platforms, classifiers) [`1de508e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1de508e4974bbc13ec6dbab86a2799bd5ff01005)


### Continuous Integration

* change the configuration of mypy to ignore `httpx` package [`6eab8ac`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6eab8acd491de95113b1cadebb62a04aa73a3d89)
* change the main GitHub action to run iSort for code style checking [`837a229`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/837a2298b781afcfc87c9bef009b899b451a9351)
* correct the main GitHub action to use `Black~=23.7.0` [`609d334`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/609d334b7a3d32d04faad0260fe8ab4a6a1add09)
* upgrade mypy to v1.4.1 and Black to v23.7.0 for improved typing and formatting [`#1685`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1685)


### Chore

* **github-actions:** update Node.js version to 18.16.1 [`b9988f6`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b9988f6dedc5a653de00bf5becc917487ce589e6)
* correct handling of base class with no `__annotations__` in `AllOptionalMetaclass` [`d9ed61f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d9ed61fdaaa32974431b41e9cce44be09bb92e79)
* correct indentation [`4af01b4`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4af01b4023cb828093f8fd9b139f76429806c7b8)
* increase line length limit to 120 characters for Black and iSort [`586fb43`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/586fb438607824899c66db66f183451fbe4a88e4)
* remove `# fmt: off`/`# fmt: on` Black directives [`c970257`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c970257087031236d33c089aeb459d1eb3f419a2)



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
