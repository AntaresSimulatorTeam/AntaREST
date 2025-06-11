Antares Web Changelog
=====================

v2.21.0 (2025-05-26)
--------------------

## What's Changed

### Features

* **ui-playlist**: update the dialog by [`2473`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2473)
* **aggregation**: streamed aggregation by [`2484`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2484)
* **workspaces**: forbid additional workspaces on desktop by [`2394`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2394)

### Bug fixes

* **scan**: use workspace and study path as key of missing studies [`2480`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2480)
* **thermal**: return `hard coal` group in lower case [`2487`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2487)
* **desktop**: allow users to create empty studies [`2488`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2488)
* **bc**: fix issue when updating `time_step` via table-mode [`2489`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2489)
* **ui-studytree**: minor fixes and improvement [`2477`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2477)
* **scan**: properly filter default workspace [`2483`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2483)
* **desktop**: use antares-solver_windows instead of rte-antares--installer-64bits [`2457`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2457)
* **study**: fix a bug when deleting all tags [`2493`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2493)
* **import**: reduce memory use when importing large files [`2500`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2500)
* **user**: allow to fetch ldap users [`2501`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2501)
* **ui-playlist**: some issues [`2495`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2495)

### Performances
* **db**: remove N+1 requests when getting users and groups list [`2490`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2490)

### Refactorings
* **login**: remove `RequestParameters` class [`2467`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2467)
* **matrix**: remove `ContextServer` and simplify `UriResolverService` [`2463`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2463)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.20.0...v2.21.0


v2.20.0 (2025-04-30)
--------------------

## What's Changed

### Features

* **ui-api, digest**: enhance `DigestDialog` and add dedicated endpoint for digest UI [`2240`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2240)
* **matrices**: allow other formats for internal matrices storage [`2113`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2113)
* **area**: move area command creation [`2322`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2322)
* **ini**: allow custom parsers/serializers for ini options [`2332`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2332)
* **matrix**: never return empty matrix [`2296`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2296)
* **properties**: add two fields to area properties form [`2347`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2347)
* **ui-matrix**: enable flexible row count configuration [`2345`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2345)
* **xpansion**: create `remove_xpansion_configuration` command [`2361`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2361)
* **renewable**: add update renewable cluster command [`2352`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2352)
* **xpansion**: introduce `create_xpansion_configuration` command [`2366`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2366)
* **st-storage**: add update st storage command [`2354`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2354)
* **xpansion**: add `remove_xpansion_resource` command [`2368`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2368)
* **ui**: update MUI theme [`2335`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2335)
* **xpansion**: add `create_xpansion_resource` commands [`2371`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2371)
* **thermal**: add update thermal cluster command [`2356`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2356)
* **ui-matrix**: add `MatrixResize` allowing columns resize on matrices [`2340`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2340)
* **xpansion**: add candidate commands [`2367`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2367)
* **binding-constraints**: create UpdateConstraints command [`2274`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2274)
* **hydro**: add update hydro management option command [`2374`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2374)
* **xpansion**: add `update_xpansion_settings` command [`2393`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2393)
* **area**: replace update config in table mode areas [`2350`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2350)
* **adequacy_patch**: update default values in adequacy patch form, in english and french view [`2402`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2402)
* **logs**: add task_id and user.id to logs [`2414`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2414)
* **hydro**: add new endpoint to get hydro related properties for the whole study [`2420`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2420)
* **variant_study**: copy variant as raw study [`2405`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2405)
* **ui-studies**: display the study list in the tree even if folder list is loading [`2427`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2427)
* **study**: copy study with specific path [`2439`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2439)
* **ui-matrix**: add copy paste and keybinds support [`2441`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2441)
* **study**: copy only selected outputs [`2447`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2447)
* **aggregator_manager**: enable aggregation size on endpoint [`2451`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2451)
* **matrix**: support matrices with headers inside the matrixstore [`2450`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2450)


### Bug fixes

* **all**: multiple warnings fix [`2318`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2318)
* **explorer**: normalize folder path [`2329`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2329)
* **commands**: fix error on command notifications [`2323`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2323)
* **st-storage**: fix ST storage groups case for v8.6 [`2342`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2342)
* **scan**: fix workspaces can't overlap nor be renamed [`2334`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2334)
* **ui-debug**: treat 'file://*.json' files as JSON instead of unsupported [`2346`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2346)
* **study-tree-ui**: add exist true filter to studies request [`2339`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2339)
* **ini**: ignore case when performing update and delete of ini files [`2353`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2353)
* **xpansion**: allow matrices normalization [`2369`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2369)
* **matrix**: change headers inside GET /raw endpoint when formatted is False [`2375`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2375)
* **all**: refactor the camel case model annotation [`2376`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2376)
* **hydro_management**: fix read and write in hydro.ini [`2370`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2370)
* **mypy**: change writing inside pandas `replace` method [`2391`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2391)
* **ui-matrix**: prevent fill handle updates for read-only matrices [`2383`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2383)
* **ui-digest**: conditionally render digest button based on synthesis availability [`2389`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2389)
* **study**: allow creating old studies with new version format [`2400`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2400)
* **perfs, variant**: avoid loading study from disk for snapshot generation [`2386`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2386)
* **areas**: allow negative spread costs [`2407`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2407)
* **bc**: allow terms writing in any case and allow area/cluster names in endpoint [`2406`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2406)
* **adequacy_patch**: fix bad tooltip [`2415`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2415)
* **study-tree-ui**: fix several bugs and major refactoring [`2348`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2348)
* **adequacy-patch**: fix serialization issue inside the ini file [`2418`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2418)
* **terms**: revert breaking change [`2421`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2421)
* **ui-matrix**: disable resize on non-timeseries matrices [`2419`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2419)
* **ui**: multiple new theme issues [`2422`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2422)
* **db**: fix relationship issues inside tests [`2429`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2429)
* **tests**: fix relative import issue [`2432`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2432)
* **commands**: use ids inside newly introduced update commands [`2424`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2424)
* **area**: fix bug on allocation and correlation views [`2434`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2434)
* **variants**: don't raise Exeptions when deleting a variant [`2437`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2437)
* **ui-adequacy-patch**: remove unwanted fields and fix display [`2436`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2436)
* **ui**: theme issues [`2443`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2443)
* **ui-studies**: folder filter hide all studies [`2445`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2445)
* **raw**: raise Exception when modifying expansion folder inside variant [`2446`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2446)
* **ui-storages**: disable resize on inflow matrix [`2442`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2442)
* **ui-matrix**: disable keybinds on read-only matrices [`2453`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2453)
* **ui-adq-patch**: fix display of `includeHurdleCostCsr` switch [`2458`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2458)
* **ui-matrix**: ensure consistent column sizing when switching between matrices [`2461`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2461)
* **aggregation**: allow aggregation for variants [`2462`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2462)
* **ui-matrix**: add aggregates columns calculation on matrix resize [`2456`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2456)
* **ui-digest**: make first column fixed [`2460`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2460)
* **ui-clusters**: handle area/cluster navigation by properly updating URL segments [`2455`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2455)
* **matrixstore**: ensure we can read legacy null matrix [`2465`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2465)
* **ui-settings**: style issues in form dialogs [`2468`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2468)
* **hydro**: allow negative values for hydro allocation coefficients [`2464`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2464)

### Performances

* **links**: improve drastically perfs for update links inside table-mode [`2381`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2381)
* **ui-results**: prevent infinite rendering in results matrices [`2388`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2388)
* **table-mode**: speed-up mass update for thermal clusters [`2416`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2416)
* **table-mode**: speed-up mass update for renewable clusters [`2423`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2423)
* **table-mode**: speed-up mass update for short term storages [`2425`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2425)

### Chore

* **group**: enforce lower case for item groups [`2333`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2333)
* **simulator**: bump simulator v8.8 version inside Desktop app [`2355`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2355)
* **deps**: use `antares-study-version` package for study creation [`2358`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2358)
* **patch**: remove patch service [`2359`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2359)
* **dev**: share pre-commit configuration for local dev [`2360`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2360)
* **typing**: add TypeAlias where missing [`2401`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2401)
* **config**: remove unused cache dict [`2404`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2404)
* **ci**: remove ubuntu20 from the ci [`2426`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2426)
* **tests**: remove useless zip and introduce new study fixtures [`2431`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2431)
* **variant**: remove obsolete `execute_or_add_commands` method [`2438`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2438)
* **outputs**: create a dedicated output service to separate concerns [`2448`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2448)


### Refactorings

* **ui-clusters**: update clusters group names to lowercase [`2341`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2341)
* **all**: remove pydantic v1 dependencies [`2344`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2344)
* **services**: fix wrong dependency from business to service [`2343`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2343)
* **thermal**: improve classes design for thermal clusters [`2430`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2430)
* **commands**: remove apply config [`2449`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2449)

### Build

* **lint**: use ruff instead of isort and black [`2349`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2349)


### Tests

* **sts, renewable**: add command dto unit tests [`2392`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2392)

### Documentation

* fix broken links and disable default expansion [`2435`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2435)
* add some docstring to some important database classes [`2440`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2440)


**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.19.2...v2.20.0


v2.19.2 (2025-03-17)
--------------------

## What's Changed

### Bug fixes

* **commands**: fix create_st_storage v1 parsing [`2408`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2408)

v2.19.1 (2025-03-11)
--------------------

## What's Changed

### Bug fixes

* **commands**: add missing index on commands table, for performances [`2373`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2373)
* **bc**: allow term modification [`2372`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2372)
* **groups**: groups in lowercase [`2377`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2377)
* **ini**: ignore case when performing update and delete of ini files [`2378`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2378)
* **commands**: remove command notifications [`2379`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2379)
* **hydro**: case insensitive read and write in hydro.ini [`2387`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2387)
* **debug**: ensure .json files with prefix file:// proper rendering [`2390`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2390)

### Perfs

* **links**: improve drastically perfs for links inside table-mode [`2384`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2384)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.19.0...v2.19.1

v2.19.0 (2025-02-10)
--------------------

## What's Changed

### Features

* **ts-gen**: add failing area and cluster info inside error msg [`2227`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2227)
* **commands**: add study_version information inside commands [`2202`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2202)
* **matrix**: allow import for comma-separated csv [`2237`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2237)
* **ui-commons,ui-api**: allow to export matrices to CSV [`2236`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2236)
* **link**: add update endpoint for link [`2175`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2175)
* **raw**: allow folder creation inside `user` folder [`2216`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2216)
* **clusters**: convert groups and names to lower case [`2182`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2182)
* **commands**: add creation timestamp and user name inside commands [`2252`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2252)
* **ui-cmd**: add command details on variants commands panel [`2265`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2265)
* **ui-debug**: add unsupported files handling [`2260`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2260)
* **aggregation-apis**: rename aggregation cols [`2250`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2250)
* **api,ui-studies**: update study move [`2239`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2239)
* **raw-api**: add an endpoint to retrieve files in their original format [`2244`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2244)
* **ui-links**: set first link as default when component mounts [`2268`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2268)
* **ui-studies**: add on click fetch and display list of non studies folder [`2224`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2224)
* **ui-debug**: add download in original file format  [`2277`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2277)
* **variant**: add reason when variant generation fails [`2290`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2290)
* **launcher**: allow local launcher to work with xpress [`2251`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2251)
* **installer**: update installer for v2.19 [`2297`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2297)
* **bc**: add constraint duplication endpoint [`2295`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2295)
* **ui-api, studies**: optimize studies listing [`2288`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2288)
* **ui-tablemode,ui-playlist**: replace Handsontable by Glide Data Grid [`2289`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2289)
* feat: add an endpoint to allow multiple deletion of binding constrain… [`2298`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2298)
* **ui-hooks**: update useSafeMemo and useUpdatedRef [`2309`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2309)
* **ui-studies**: sort study tree folders [`2300`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2300)
* **study**: normalize study path [`2316`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2316)
* **feat(ts-gen)**: replace legacy endpoints with new ones [`2303`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2303)
* **ui-commons**: allow multiple cells to be pasted in DataGridForm [`2328`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2328)


### Bug fixes

* **link**: fix empty string handling in filter conversion [`2232`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2232)
* **ci**: use fixed versions for gh actions for build stability [`2255`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2255)
* **links**: fix a bug that occurred when updating links via table-mode [`2256`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2256)
* **tasks**: fix frozen task with load balanced pgpool [`2263`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2263)
* **ui-bc**: use `matrixindex` timesteps for row display [`2262`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2262)
* **xpansion**: fix several issues related to weights and constraints [`2273`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2273)
* **ui**: fix untranslated message [`2275`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2275)
* **link**: add comment attribute in link that was missing and causing an 422 error [`2281`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2281)
* **matrix**: remove columns full of `NaN` inside matrices at the import [`2287`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2287)
* **matrix**: return default empty matrix even when called with formatted=False [`2286`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2286)
* **list_dir**: check permissions and consider workspace filters config [`2279`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2279)
* **raw**: change bytes serialization when formatting is False [`2292`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2292)
* **desktop**: fixes calendar issue when reading matrices on Linux [`2291`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2291)
* **disk-usage**: suppress exceptions [`2293`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2293)
* **study-tree**: fix tooltip message key [`2306`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2306)
* **matrix**: allow odd matrix format when importing [`2305`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2305)
* **ui**: resolve sonar complexity warning [`2311`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2311)
* **ui-studies**: display 'default' workspace even if empty [`2301`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2301)
* **ui-studies**: 615 minor fixes [`2314`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2314)
* **bc**: fix a bug that would occurs after deleting multiple bc [`2317`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2317)
* **ui-tablemode**: adjust the size of the column with the initial data [`2320`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2320)
* **ui-tablemode**: prevent small values from being cut off and remove empty space at the bottom [`2321`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2321)
* **ui-commons**: keep auto size for DataGrid [`2324`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2324)


### Chore

* **upgrader**: remove duplicated tests [`2235`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2235)
* **commands**: fix user name display in commands [`2284`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2284)
* **ui**: update license year [`2307`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2307)
* **ui**: bump vite from 5.4.8 to 5.4.14 [`2308`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2308)
* **ui**: disable TS null assertion and update the code that use it [`2312`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2312)
* **commands**: remove obsolete variant-related features [`2326`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2326)
* **ui-common**: bump MUI to v6.4.3 to resolve Select list bug causing crashes [`2330`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2330)
* **all**: bump pydantic and linting packages [`2331`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2331)
* **copyright**: Update year in copyright headers [`2299`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2299)

### Continuous integration

* **commitlint**: add new rules for scope [`2319`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2319)
* **mypy**: enforce explicit overrides [`2270`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2270)
* **github**: add PR title lint job [`2304`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2304)


### Breaking changes

* **ts-gen**: replace legacy endpoints with new ones [`2303`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2303)


**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.18.3...v2.19.0-test

v2.18.3 (2024-12-17)
--------------------

## What's Changed

### Bug Fixes

* **ui-results**: resolve data misalignment in matrix column filtering [`2269`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2269)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.18.2...v2.18.3


v2.18.2 (2024-12-11)
--------------------

## What's Changed

### Bug Fixes

* **tasks**: frozen tasks with pgpool [`2264`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2264)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.18.1...v2.18.2

v2.18.1 (2024-12-02)
--------------------

## What's Changed

### Bug Fixes

* **ui-tablemode**: style missing [`2257`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2257)
* **ui-studies**: multiple API calls on study list view [`2258`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2258)
* **events**: avoid slow processing of events [`2259`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2259)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.18.0...v2.18.1


v2.18.0 (2024-11-29)
--------------------

## What's Changed

### Features

* **ui-common**: integrate `GlideDataGrid` into `MatrixGrid` [`2134`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2134)
* **pydantic**: use pydantic serialization [`2139`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2139)
* **aggregation-api**: delete index from the response file [`2151`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2151)
* **variant**: add new endpoint to clear snapshots [`2135`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2135)
* **version**: use class StudyVersion to handle versions [`2156`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2156)
* Increase cleaning snapshot frequency [`2173`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2173)
* **tests**: add tests on matrix index [`2180`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2180)
* **desktop**: open browser when server is started [`2187`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2187)
* **ui-tablemode**: prevent duplicate columns [`2190`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2190)
* **watcher**: filter out upgrade and TS generation `.tmp` folders [`2189`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2189)
* **installer**: update installer version and improve desktop version launcher [`2157`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2157)
* **tasks**: add new endpoint to fetch task progress [`2191`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2191)
* **bc**: use `update_config` instead of `update_bc` for multiple updates [`2105`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2105)
* **ts-gen**: display progress bar via websockets [`2194`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2194)
* **watcher**: add new endpoint for optimized scanning [`2193`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2193)
* **ui-ts**: update TimeSeriesManagement page to allow the generation of TS [`2170`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2170)
* **matrices**: allow csv import [`2211`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2211)
* **matrix**: allow import for various formats [`2218`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2218)
* **ui-results**: enhance results columns headers [`2207`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2207)
* **auto_archive_service**: increase cleaning snapshot frequency [`2213`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2213)
* **ui-study**: change error display in FreezeStudy [`2222`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2222)
* **ui-settings**: allow to change app language [`2226`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2226)
* **ui-results**: add column filters [`2230`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2230)
* **ts-gen**: add failing area and cluster info inside error msg (#2227) [`2231`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2231)
* Add new build directory structure [`2228`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2228)
* **installer**: update installer for new directory layout [`2242`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2242)
* **ui-studies**: allow to move an archived study [`2241`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2241)
* **ui-i18n**: change translations for thermal fields [`2246`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2246)

### Bug Fixes

* **ci**: multiply timeouts on windows platform [`2137`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2137)
* **playlist**: change response model to accept optional answers [`2152`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2152)
* **api**: allow `nominalcapacity` to be a float inside API response [`2158`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2158)
* **adq_patch**: set default value for field `enable-first-step` to False [`2160`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2160)
* **pydantic**: allow `str` fields to be populated by `int` [`2166`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2166)
* **api**: allow `min_stable_power` to be a float inside API response [`2167`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2167)
* **snapshot_cleaning**: set `ref_id` to `None` to prevent postgresql crash [`2169`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2169)
* **allocation**: show matrix even with only one area [`2168`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2168)
* Enable foreign keys for sqlite [`2172`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2172)
* **matrix-index**: return the right year [`2177`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2177)
* **tests**: adapt new year for index test [`2178`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2178)
* **db**: migrate db to use foreign key inside sqlite [`2185`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2185)
* Apidocs redirect [`2186`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2186)
* **bc**: display matrix index according to frequency [`2196`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2196)
* **docker**: reduce docker image size [`2195`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2195)
* **xpansion**: fix typo inside backend api call [`2197`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2197)
* **matrix**: return empty index for empty matrices [`2198`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2198)
* **archive**: raise Exception when (un)archiving wrong outputs [`2199`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2199)
* **installer**: update installer to fix install to wrong directory [`2205`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2205)
* **ts-gen**: add failing info in the front and fix pandas issue in the back [`2208`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2208)
* **ui-ws**: rename the task progress event type [`2209`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2209)
* **export**: allow digest file download [`2210`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2210)
* **ui-maps**: area positions are not saved [`2212`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2212)
* **ts-gen**: bump package to avoid `fo_rate` or `po_rate` exceptions [`2215`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2215)
* **ui**: progress bar issue [`2217`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2217)
* **ui-ts**: submit partial values instead of all [`2223`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2223)
* **ui-tasks**: add missing new task notifications [`2225`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2225)
* **ts-gen**: make variant generation fail when it's supposed to [`2234`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2234)
* **desktop,windows**: wait a few seconds for browser to open [`2247`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2247)
* **outputs**: allow reading inside archive + output with `.` in the name [`2249`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2249)
* **export**: allow export for zipped outputs [`2253`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2253)

### Continuous Integration

* **tests**: reduce number of workers for tests [`2149`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2149)

### Documentation

* Improve of the documentary tree and make some update [`2243`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2243)

### Build

* **python**: bump project dependencies [`1728`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1728)
* **ui**: fix rollup issue [`2161`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2161)
* **ui**: fix issue with build result not working [`2163`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2163)
* **deps**: bump launcher and paramiko versions [`2140`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2140)
* **python**: bump python version to use v3.11 [`2164`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2164)

### Chore

* **front-end**: add license headers inside front-end [`2145`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2145)
* **variants**: increase timeout duration for variant generation [`2144`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2144)
* **license**: add a new ESLint rule to check license header [`2150`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2150)

### Perf

* **scripts**: improve load balancing [`2165`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2165)

### Style

* **license**: reformat license header inside front-end [`2148`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2148)
* **api**: change apidoc example to make it work [`2155`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2155)
* **variant**: improve logs [`2179`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2179)

### Refactor

* **workers**: remove the `simulator` worker [`2184`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2184)
* **ui**: replace `MatrixInput` with `Matrix` Glide Data Grid integration [`2138`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2138)
* **aggregation-apis**: remove `time` column from the aggregated data [`2214`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2214)

### Test

* **ui-utils**: add tests for validation utils & refactor imports [`2192`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2192)

### BREAKING CHANGES

* **archive-apis**: use `.7z` format to archive studies [`2013`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2013)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.17.6...v2.18.0

v2.17.6 (2024-09-25)
--------------------

## What's Changed

### Features

* **upgrader**: use `antares-study-version` package [`2108`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2108)
* **ts-gen**: add timeseries generation [`2112`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2112)
* **bc**: show existing matrices only [`2109`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2109)
* **aggregation-api**: add new endpoint for `economy/mc-all` aggregation [`2092`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2092)
* **installer**: add installer as a submodule [`2110`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2110)
* **ui-debug**: update the view [`2093`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2093)

### Bug Fixes

* **ui-areas**: add correct unit in title in Properties form [`2115`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2115)
* **hydro**: wrong frequency for inflow pattern [`2116`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2116)
* **adequacy-patch**: csr relaxation must be an integer [`2123`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2123)
* **launcher-api**: remove orphan JobResults visibility permissions [`2128`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2128)
* **ui**: add missing `i18n` key and styles on `EmptyView` [`2127`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2127)

### Continuous integration

* **github**: split npm jobs and add dependency caching [`2118`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2118)
* **test**: parallel pytest execution [`2133`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2133)

### Documentation

* Add installer directions [`2114`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2114)

### Build

* Move all build and project configuration to pyproject.toml [`2122`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2122)
* Use relative paths in coverage report [`2125`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2125)
* Remove auto-generated changelog from desktop package [`2126`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2126)

### Chore

* Fix licensing-related issues [`2132`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2132)
* Add license headers for projects files [`2130`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2130)

### BREAKING CHANGES

* **aggregation-api**: add new endpoint for `economy/mc-all` aggregation [`2092`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2092)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.17.5...v2.17.6

v2.17.5 (2024-08-05)
--------------------

### Bug Fixes

* **sonar:** resolve sonar security issues [`2098`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2098)
* **sc_builder:** make section case insensitive [`2106`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2106)
* **output:** endpoint GET `/variables` works with no `areas` or `links` folder [`2107`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2107)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.17.4...v2.17.5

v2.17.4 (2024-07-29)
--------------------

### Features

* **output:** enhance output synthesis view [`2088`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2088)
* **ui-study:** add button to display 'digest' file on successful tasks in task list [`2101`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2101)
* **ui-bc:** increases constraint terms field size [`2102`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2102)
* **bc:** avoid unnecessary creation of RHS matrices for binding constraints [`2077`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2077)
* **ui-results:** add button to display 'digest' file in result list [`2103`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2103)

### Bug Fixes

* **area:** allow removal when aggregated mode used [`2094`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2094)
* **ui-map:** prevent name field to overflow dialog box and add more space [`2102`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2102)

**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.17.3...v2.17.4

v2.17.3 (2024-07-18)
--------------------

### Features

* **api:** do not allow areas, links or thermals deletion when referenced in a binding constraint [`2061`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2061)
* **outputs:** build outputs tree based on filesystem [`2064`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2064)
* **api-raw:** raise a 404 Not Found error when a resource is missing in the study [`2078`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2078)

### Bug Fixes

* **ui-clusters:** improve cell number values accuracy by using rounding instead of truncating [`2087`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2087)
* **ui-commons:** prompt from Form displayed on dialog validation [`2089`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2089)

### Continuous integration

*  **workflows:** update Actions in GitHub workflows [`2080`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2080)

### Documentation

* **user-guide:** updating Binding Constraints Commands documentation and metadata for search [`2082`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2082)
* **user-guide:** improve the user guide and add "How to Create a New Study?" topic [`2081`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2081)


**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.17.2...v.2.17.3


v2.17.2 (2024-06-19)
--------------------

### Features

* **ui-api:** add scenario builder v8.7 full support [`#2054`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2054)
* **api,ui-config:** add 'MILP' value option in 'Unit Commitment Mode' field for study >= v8.8 [`#2056`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2056)
* **outputs:** remove useless folder `updated_links` [`#2065`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2065)
* **ui:** add save button static at bottom and fix style issues [`#2068`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2068)
* **ui-theme:** increase scrollbar size [`#2069`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2069)
* **desktop:** add desktop version for ubuntu 22 [`#2072`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2072)

### Bug Fixes

* **variants:** display variants in reverse chronological order in the variants tree [`#2059`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2059)
* **table-mode:** do not alter existing links that are not updated [`#2055`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2055)
* **bc:** only remove terms when asked [`#2060`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2060)
* **table-mode:** correct the update of the `average_spilled_energy_cost` field in table mode [`#2062`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2062)
* **ui:** hide "upgrade" menu item for variant studies or studies with children [`#2063`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2063)
* **ui-commons:** display a popup to warn of unsaved modifications on Form [`#2071`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2071)

### Continuous integration

* **worker:** deploy AntaresWebWorker on its own [`#2066`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2066)
* **sonar:** bump github action download artifact [`#2070`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2070)


**Full Changelog**: https://github.com/AntaresSimulatorTeam/AntaREST/compare/v2.17.1...v2.17.2


v2.17.1 (2024-06-10)
--------------------

### Features

* **launcher:** add new API endpoint `/v1/launcher/time-limit` and update `LauncherDialog` [`#2012`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2012)
* **raw:** refactor aggregation endpoint [`#2031`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2031)
* **ui-common:** add validation message in ImportDialog and update style [`#2040`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2040)
* **ui-studies:** add studies "archive" tag [`#2043`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2043)
* **ui:** add a the new split view on multiple pages [`#2046`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2046)
* **desktop**: update Antares Web Desktop version [`#2036`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2036)
* **ui-thermal:** minor adjustments to v8.7 `Thermal` fields [`#2053`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2053)
* **ui-bc:** add empty screen [`#2052`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2052)
* **ui-bc:** prevent `404` error after deletion of the current or last constraint [`#2052`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2052)


### Bug Fixes

* **import:** allow import for users that are reader only [`#2032`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2032)
* **variant-command:** correct behavior of creation command in special context [`#2041`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2041)
* **ui-study:** prevent `CreateVariantDialog` fields overflow [`#2044`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2044)
* **ui-commons:** add of extensions accepted for matrix import in MatrixInput [`#2048`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2048)
* **api-aggregation:** raise 404 HTTP exception for unfound output names [`#2050`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2050)
* **scenario-builder:** handle missing objects in Scenario Builder configuration [`#2038`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2038)
* **variants:** display variants in chronological order in the variants tree [`#2049`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2049)
* **upgrade:** raise an HTTP 417 exception when an upgrade has unmet requirements [`#2047`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2047)
* **ui-study:** disable `Areas` tab when no areas are present to prevent incorrect component display [`#2052`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2052)
* **api-bc:** ensure removal of the last term in binding constraints [`#2052`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2052)


### Refactoring

* **ui-storages:** short-term storage update form [`#2025`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2025)


### Build System

* **pyinstaller:** upgrade version of pyinstaller in build requirements [`#2030`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2030)


v2.17 (2024-05-15)
------------------

Support for evolutions relating to studies in versions 8.7:
- Scenarized RHS for binding constraints,
- Thermal cluster new properties (cost generation mode, efficiency, variable OM cost)

Support for evolutions relating to studies in versions 8.8:
- Short-term storage¶: add `enabled` property
- Experimental "MILP" mode (using launcher options)

### Features

* **bc:** add endpoint for multiple terms edition [`#2020`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2020)
* **table-mode:** add missing properties for v8.6 and 8.7 [`#1643`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1643)
* **ui-table-mode:** translate table types in add/edit modal


### Bug Fixes

* **bc:** handle undefined v8.3 fields [`#2026`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2026)
* **table-mode:** hide `adequacy_patch_mode` column from table-mode before v8.3 [`#2022`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2022)
* **ui-common:** allow only import of TSV file in `MatrixInput` [`#2027`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2027)
* **ui-settings:** prevent false duplicates on group form updates [`#1998`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1998)
* **ui-table-mode:** reset 'column' field when 'type' field change in create/update modal
* **ui-table-mode:** unable to edit tables with old types
* **ui-table-mode:** add missing "ST Storage" in Table Mode template [`#2016`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2016)
* **download**: improve performance of Excel file download


v2.16.8 (2024-04-19)
--------------------

### Features

* **clusters:** add new endpoint for clusters duplication [`#1972`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1972)
* **clusters (ui):** implement new duplication endpoint and optimistic update [`#1984`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1984)
* **configuration:** turn Thematic Trimming variable names in upper case
* **configuration (ui):** replace underscore with space in Thematic Trimming variable names [`#2010`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2010)
* **ui:** enhance and refactor validation across UI components [`#1956`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1956)

### Bug Fixes

* **clusters (ui):** totals are updated after a duplication and a deletion [`#1984`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1984)
* **clusters (ui):** issue with selecting and deleting rows [`#1984`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1984)
* **st-storages (ui):** correction of incorrect wording between "withdrawal" and "injection" [`#1977`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1977)
* **st-storages (ui):** change matrix titles [`#1994`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1994)
* **st-storages:** use command when updating matrices [`#1971`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1971)
* **variants:** avoid recursive error when creating big variant tree [`#1967`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1967)
* **outputs:** build outputs config even when using cache [`#1958`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1958)
* **comments:** use a command to update comments on a variant [`#1959`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1959)
* **outputs (ui):** correct weekly data formatting to support 53-week years [`#1975`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1975)
* **configuration:** add missing variables in Thematic Trimming for studies in version v8.6 or above [`#1992`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1992)
* **configuration:** version availability for "STS Cashflow By Cluster" variable is v8.8
* **launcher:** upgrade the project dependencies to use Antares-Launcher v1.3.2
  - **ssh:** add retry loop around SSH Exceptions [`#68`](https://github.com/AntaresSimulatorTeam/antares-launcher/pull/68)
  - **retriever:** avoid infinite loop when `sbatch` command fails [`#69`](https://github.com/AntaresSimulatorTeam/antares-launcher/pull/69)
* **synthesis:** prevent 500 error during study synthesis parsing [`#2011`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/2011)


v2.16.7 (2024-03-05)
--------------------

### Bug Fixes

* **desktop:** correct configuration and launcher load indicator for Antares Web Desktop [`#1969`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1969)


v2.16.6 (2024-03-04)
--------------------

### Features

* **ui-tasks:** add launcher metrics [`#1960`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1960)
* **ui-tasks:** auto refresh launcher metrics [`#1963`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1963)


### Bug Fixes

* **ui-results:** adjust date times for accurate frequency display [`#1960`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1960)
* **ui-common:** matrices display issues [`#1960`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1960)
* **ui-common:** download latest value of matrices [`#1962`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1962)


v2.16.5 (2024-02-29)
--------------------

### Features

* **ui-results:** add results matrix timestamps [`#1945`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1945)


### Bug Fixes

* **ui-hydro:** add missing matrix path encoding [`#1940`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1940)
* **ui-thermal:** update cluster group options to handle `Other 1` [`#1945`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1945)
* **ui-results:** prevent duplicate updates on same toggle button click [`#1945`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1945)
* **ui-results:** disable stretch to fix display issue [`#1945`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1945)
* **ui-hydro:** disable stretch to fix display issue on some matrices [`#1945`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1945)
* **variants:** correct the generation of variant when a snapshot is removed [`#1947`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1947)
* **tags:** resolve issue with `study.additional_data.patch` attribute reading [`#1944`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1944)
* **study:** correct access to study `additional_data` [`#1949`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1949)
* **ui-tablemode:** create modal is frozen when submitting without column [`#1946`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1946)
* **ui-tablemode:** 'co2' column not working [`#1952`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1952)
* **ui:**  add missing i18n dependency [`#1954`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1954)


v2.16.4 (2024-02-14)
--------------------

### Features

* **api-ui:** add Inflow Structure form in Hydro [`#1919`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1919)
* **db:** index tables to improve study search and sorting performance [`#1902`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1902)
* **packaging:** update the packaging script to use Antares Solver v8.8.2 [`#1910`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1910)
* **service:** use slurm `sinfo` command to improve "cluster load" indicator [`#1664`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1664)
* **study-search:** optimize the studies search engine [`#1890`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1890)
* **tags-db:** add `tag` and `study_tag` tables to the db (migration) [`#1923`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1923)
* **tags-db:** update tags related services and endpoints [`#1925`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1925)
* **ui-disk-usage:** add disk usage to study details [`#1899`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1899)


### Bug Fixes

* **api-model:** correct `AllOptionalMetaclass` for field validation in form models [`#1924`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1924)
* **bc:** correct case sensitivity for binding constraint term IDs [`#1903`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1903)
* **config:** add Swagger proxy settings in Vite configuration [`#1922`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1922)
* **disk-usage:** correct disk usage calculation for study variants with simulation results [`#1926`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1926)
* **disk-usage:** fix bug on variants [`#1915`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1915)
* **packaging:** fix packaging script for Windows (issue with Vite.js) [`#1920`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1920)
* **thermals:** correct the default value of the "gen-ts" property to use "use global" instead of "use global parameter" [`#1918`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1918)
* **ui-home:** load synthesis to get areas and links count [`#1911`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1911)
* **ui-hydro,storage:** correct labels and units in forms [`#1928`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1928)
* **ui-map:** reload map data on study revisit [`#1927`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1927)

### Build System

* **packaging:** issue with desktop app packaging [`#1912`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1912)
* **vite:** replace create-react-app by Vite [`#1905`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1905)


v2.16.3 (2024-01-17)
--------------------

### Features

* **api-filesystem:** add new API endpoints to manage filesystem and get disk usage [`#1895`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1895)
* **ui-district:** enhance Scenario Playlist loading and remove Regional District menu  [`#1897`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1897)


### Bug Fixes

* **config:** use "CONG. PROB" for thematic trimming (fix typo) [`#1893`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1893)
* **ui-debug:** correct debug view for JSON configuration [`#1898`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1898)
* **ui-debug:** correct debug view for textual matrices [`#1896`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1896)
* **ui-hydro:** add areas encoding to hydro tabs path [`#1894`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1894)


### Refactoring

* **ui-debug:** code review [`#1892`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1892)


### Continuous Integration

* **docker:** add the `ll` alias in `.bashrc` to simplify debugging [`#1880`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1880)


v2.16.2 (2024-01-10)
--------------------

### Features

* **bc:** add input validation for binding constraint creation [`#1868`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1868)
* **study-size:** add new route to get a study disk usage (in bytes) [`#1878`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1878)
* **table-mode:** update Table Mode view [`#1883`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1883)
* **thermals, st-storages:** add a dialog to define a name when duplicating a cluster or a storage [`#1866`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1866)
* **debug-view:** introduce advanced `JSONEditor` and `Debug` view updates [`#1885`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1885)


### Performance

* **db:** improve performance by using joins instead of N+1 queries [`#1848`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1848)
* **raw-study:** improve INI file reading performance for RAW studies [`#1879`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1879)


### Bug Fixes

* **bc:** automatically change binding constraint matrix when changing frequency [`#1867`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1867)
* **ci:** avoid reflecting user-controlled data (SonarCloud issue) [`#1886`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1886)
* **db:** correct alembic migration script used to purge obsolete tasks [`#1881`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1881)
* **db:** add missing constraints and relationships in `TaskJob` table [`#1872`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1872)
* **services:** ensure all worker services run indefinitely [`#1870`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1870)
* **study-factory:** ignore non-existent files in archived studies during build [`#1871`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1871)
* **thermals:** correct TS Generator matrix index for thermal clusters [`#1882`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1882)
* **ui:** prevent synchro issues between tabs and react-router [`#1869`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1869)
* **xpansion:** update for improved parameter handling and code refactoring [`#1865`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1865)


### Documentation

* **st-storage:** add ST-Storage documentation [`#1873`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1873)


### Tests

* remove Locust dependency and unit tests (not really useful) [`34c97e0`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/34c97e05fe8a623a799cd31519b7982dae579368)


### Refactoring

* **bc:** remove duplicate class BindingConstraintType [`#1860`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1860)


v2.16.1 (2023-12-14)
--------------------

### Features

* **ui:** add manual submit on clusters form [`#1852`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1852)
* **ui-modelling:** add dynamic area selection on Areas tab click [`#1835`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1835)
* **ui-storages:** use percentage values instead of ratio values [`#1846`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1846)
* **upgrade:** correction of study upgrade when upgrading from v8.2 to v8.6 (creation of MinGen) [`#1861`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1861)


### Bug Fixes

* **bc:** correct the name and shape of the binding constraint matrices [`#1849`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1849)
* **bc:** avoid duplicates in Binding Constraints creation through REST API [`#1858`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1858)
* **ui:** update current area after window reload [`#1862`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1862)
* **ui-study:** fix the study card explore button visibility [`#1842`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1842)
* **ui-matrix:** prevent matrices float values to be converted [`#1850`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1850)
* **ui-matrix:** calculate the prepend index according to the existence of a time column [`#1856`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1856)
* **ui-output:** add the missing "ST Storages" option in the Display selector in results view [`#1855`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1855)


### Performance

* **db-init:** separate database initialization from global database session [`#1837`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1837)
* **variant:** improve performances and correct snapshot generation [`#1854`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1854)


## Documentation

* **config:** enhance application configuration documentation [`#1710`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1710)


### Chore

* **deps:** upgrade material-react-table [`#1851`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1851)



v2.16.0 (2023-11-30)
--------------------

### Features

* **api:** add renewable clusters to API endpoints [`#1798`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1798)
* **api:** add endpoint get_nb_cores [`#1727`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1727)
* **api-raw:** add the `create_missing` flag to allow creating missing files when uploading a file [`#1817`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1817)
* **api-storage:** update initial level field default value [`#1836`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1836)
* **api-thermal:** add clusters management endpoints [`2fbfcfc`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2fbfcfc83b7b4df3ad59f602ab36336b8d3848fa)
* **api-thermal:** delay the import of `transform_name_to_id` [`1d80ecf`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1d80ecfa844bf6f20fe91977764a529858b2c5ce)
* **api-thermal:** implement the `__repr__` method in enum classes for easier debugging [`7e595a9`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7e595a90555750b72401c99a21eaac2e88419015)
* **api-thermal:** improve the `ThermalClusterGroup` enum to allow "Other 1" and "Other" values for the `OTHER1` option [`c2d6bc1`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c2d6bc1be72ad722aea1dccc61779a5d25c52786)
* **binding-constraint:** add the binding constraint series in the matrix constants generator [`c1b4667`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c1b4667dcb2ebcce0a4225030888efa392d6b109)
* **common:** add dynamic size for GroupedDataTable [`116c0a5`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/116c0a5743d434aa40975c8c023ab8c545ad9d49)
* **job-result-dto:** the `JobResultDTO` returns the owner (ID and name) instead of owner ID [`a53d1b2`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a53d1b21a024b9fc3ba0cfbde8f9396917165b18)
* **launcher:** add information about which user launched a study [`#1761`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1761)
* **launcher:** unzipping task raised by the user who launched the study [`f6fe27f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f6fe27fdabf052a70c55c357b235e7692ac83064)
* **launcher:** allow users with `Permission.READ` or above to unzip a study [`4568b91`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4568b9154cc174de1a430805b6378234bc2c3584)
* **model:** handling binding constraints frequency in study configuration parsing [`#1702`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1702)
* **model:** add a one-to-many relationship between `Identity` and `JobResult` [`e9a10b1`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e9a10b1e1c45e248ba4968d243cf0ea561084924)
* **model:** handling binding constraints frequency in study configuration parsing [`1702`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1702) [`02b6ba7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/02b6ba7a8c069ce4e3f7a765aa7aa074a4277ba5)
* **permission:** update permission types, replaced DELETE with WRITE for improved study control [`#1775`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1775)
* **requirements:** add py7zr to project requirements [`e10622e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e10622ef2d8b75b3107c2494128c92223dda5f6d)
* **simulation-ui:** use API to get launcher number of cores [`#1776`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1776)
* **st-storage:** allow all parameters in endpoint for short term storage creation [`#1736`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1736)
* **tests:** add integration tests for outputs import [`a8db0b4`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a8db0b42db3a7e334125ec591b193acaae04c37b)
* **thermal:** refactor thermal view [`#1733`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1733)
* **ui:** reduce studies header height [`#1819`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1819)
* **ui:** update LauncherDialog [`#1789`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1789)
* **ui-areas:** add version check for storage tab [`#1825`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1825)
* **ui-common:** add missing areaId param to routes [`4c67f3d`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4c67f3d9b84e38ebe5e560892319f779806d5af9)
* **ui-common:** add missing areaId param to routes [`3f09111`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3f09111541c8a55bb5e36fccb6cc547a14601ad5)
* **ui-launcher:** block launch button if cores info cannot be get [`4267028`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4267028ae0ba719b349c30007273108ec4a1407e)
* **ui-model:** add validation rules for thermal renewable and storage forms [`86fe2ed`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/86fe2ed30f3c0494306c38713a6f96e856eb003a)
* **ui-model:** check integer fields [`da314aa`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/da314aa31707f33359a9a495588d376d3f6824ce)
* **ui-npm:** update packages [`7e08826`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7e08826bf1fa62c07445905fd7ba978fa7d4cba6)
* **ui-renewables:** add new list view [`#1803`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1803)
* **ui-storages:** add storages list view and form [`#1791`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1791)
* **ui-studies:** rework study launch dialog [`#1784`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1784)
* **ui-studies:** update launcher dialog xpansion field [`011fbc6`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/011fbc689f45c06c381fbb4efb6f7bd0dedb1da6)
* **ui-thermal:** update thermal clusters list view and form labels [`#1807`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1807)
* **ui-thermal:** minor user experience improvements [`5258d14`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5258d14484feca50e452a69dd265860141804888)
* **ui-thermal:** update thermal cluster view with new component [`eb93f72`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/eb93f72301c3823b2afffff3543d8008abc8962f)
* **ui-thermal:** minor improvements [`4434d7c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4434d7c0cc73cf9e86350fc3da4ea3df6d059054)
* **ui-thermal:** add type for cluster capacity [`10aaea3`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/10aaea3009500a8a69e6d6f3ba3f496c4fdd47d3)
* **ui-thermal:** add error display on thermal clusters list [`92e3132`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/92e3132c30e216d4b075d6af028c1e38031dde9f)
* **upgrade:** denormalize study only when needed [`931fdae`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/931fdae3b2b05abad035c62b61edcb831171a5e5)
* **utils:** add 7z support for matrices import [`d53a99c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d53a99c27056fd9785b2659ab8805232b8d546fe)
* **utils:** support 7z import for studies, outputs and matrices [`a84d2aa`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a84d2aa29f0346c68226b58a3b97e1df7a1b1db9)
* **utils:** add integration test for 7z study import [`1f2da96`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1f2da96cd3ef16f7b7d5546a68d4e807a63866a4)
* **utils:** add support for .7z [`0779d88`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0779d8876137db432194d5eb3280bbf9fd495538)


### Performance

* **api-study:** optimize study overview display in Antares Web [`52cf0ca`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/52cf0ca0b54886b87d336facc52409224894b17b)
* **role-repository:** optimize the query used in `get_all_by_user` to fetch roles and groups at once [`dcde8a3`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/dcde8a30d4c4f96a33d33a4b0156519eb4fa4647)
* **study-factory:** `FileStudy` creation is done with a file lock to avoid that two studies are analyzed at the same time [`0bd9d5f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0bd9d5f7ae47f4ecc871fb0a34bde433f3659856)
* **variant:** correct slow variant study snapshot generation [`#1828`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1828)


### Bug Fixes

* **matrix:** matrix ID validator now raise an exception if the ID is empty [`d483198`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d483198ea5891081e524d10242a2330e4c9c0116)
* **raw-study:** correct matrix list generation for thermal clusters to handle non-lowercase IDs [`db86384`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/db863844fc6d1af6d61ff8401fbeccef9645b799)
* **role-type:** correct implementation of the `__ge__` operator [`379d4ae`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/379d4aee4685096cbf86879050c2fd1d87fdc5d1)
* **service:** allow unzipping with permission read [`0fa59a6`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0fa59a6da29e6524b819b5949780e48d0dd9df48)
* **st-storage:** the `initial_level` value must be between 0 and 1 [`#1815`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1815)
* **tests:** fix unit test and refactor integration one [`6bbbffc`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6bbbffc5213e996098239174c7611be979d0cb45)
* **ui:** update dynamic areaId segment URL path on area change [`#1811`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1811)
* **ui:** i18next API change [`e8a8503`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e8a8503cb24ddd543196cd7bddc6ec03b140bc1c)
* **ui:** TS issues [`ff8e635`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ff8e6357d25d02d07a28bafd8e8223f41a33ce84)
* **ui:** immer import change [`d45d274`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d45d274a316f990d60c3d6a6b54b2a8827618be3)
* **ui:** correct merge conflict imports [`77fd1ad`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/77fd1ad68a1337bef05cb8e094321f693162f193)
* **ui-common:** add case check for name in GroupedDataTable [`586580b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/586580b320a3cfb0a6e48ae3e0b2d5d1db6c68aa)
* **ui-lancher:** cores limit cannot be break [`d3f4b79`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d3f4b792780a7662330fb3c6869dc2812e1c249e)
* **ui-launcher:** add API values for min max number of cores [`ea188b1`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ea188b1fc8934769f314a43a8a27a5b3f9601f0f)
* **ui-study:** prevent study tasks list to contain all studies tasks [`#1820`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1820)
* **ui-tasks:** filter deleted studies jobs [`#1816`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1816)
* **ui-thermal:** update regex to prevent commas in id [`b7ab9a5`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b7ab9a5a1bfb004a369a7df33e35eac5729c4056)
* **ui-thermal:** update regex to avoid ReDoS vulnerabilities [`c837474`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c837474f882559cd0a283e300db364603806c002)
* **xpansion:** add missing `separation_parameter` field in the settings [`#1831`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1831)


### Documentation

* **api-thermal:** add the documentation of the thermal cluster endpoints [`c84c6cd`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c84c6cd5db7412c55d0947eaec374c808dc78bb8)
* **api-thermal:** improve the documentation of the thermal manager [`099e4e0`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/099e4e0535b7491edd1d8d0fef268137dec9e704)
* **api-thermal:** correct thermal manager doctrings [`3d3f8c3`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3d3f8c343f7192d904a9f225c4cf9e836c4ee8e2)
* **how-to:** add a "How to import a compressed study?" topic in the documentation [`28c654f`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/28c654f7493db54beccfbf640b95b0aeda874e31)
* **import-api:** improve the documentation of the import API [`f1f2112`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f1f2112e92d946002bab16c26e7cbe6a0d6945c5)
* **rtd:** correct the configuration for ReadTheDocs [`#1833`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1833)
* **study-service:** improve documentation of the `StudyService` class [`3ece436`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3ece4368eb14f77027a575ed8b2b2e9ffc2bbcb5)
* **upgrade:** add little documentation [`7075ed8`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7075ed83b0aa298c91bfc736b23a3e83901a2f24)


### Tests

* correct `test_commands_service`: ensure the admin user is in database [`#1782`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1782)
* add the `DbStatementRecorder` class to record SQL statements in memory to diagnose the queries performed by the application [`c02a839`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c02a839d9f16eb757f1bac7fdce3e4572bf102d2)
* add unit tests for `antarest.core.utils.utils.extract_zip` [`4878878`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/48788783dc24519926b1b6517ed45be3fc1deee9)
* add the `compare_elements` function to compare two XML and find differences [`15753e3`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/15753e3cb6fc9d66993c00227e02d9f3d10cc89e)
* **api:** added end-to-end test to ensure seamless functionality of API endpoints with the "bot" token [`#1770`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1770)
* **api-user:** correct API endpoint `user_save` [`483d639`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/483d63937b1325a3b98ca4fcad4b6f75c18cc15e)
* **apidoc:** add unit test for apidoc page [`#1797`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1797)
* **integration:** simplify the `app` fixture used in integration tests and add comments [`e48ce6d`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e48ce6d9c8dfd30d117f5af853d0179e49418c85)
* **login-service:** refactor unit tests to use fixture instead of mocks [`02f20f0`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/02f20f001c3612969b680c904bf6d22d5a9786da)
* **matrix-dataset:** correct unit test `test_watcher` [`d829033`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d82903375b8d83b8dde30e6d8637825602708b7c)
* **matrix-dataset:** correct unit test `test_dataset_lifecycle` [`da6f84b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/da6f84be183902428db61ad227fc3c98df29d8bb)
* **model:** correct and improve the `TestLdapService` unit tests [`84c0c05`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/84c0c05c96e9a73ca45e004d1f5cc5f4fbb58218)
* **model:** don't decorate model classes with `@dataclass` [`82d565b`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/82d565b4423281bf41782201cceef34b3d5b29dc)
* **study-comments:** add integration tests for study synthesis endpoint [`f56a4ae`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f56a4ae1b565843d1a58db60d10c945ea0c6e657)
* **study-comments:** add integration tests for study comments endpoints [`3eb1491`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3eb1491aca9b84a6beb2007a8e0977679a560e4c)
* **study-comments:** remove deprecated integration tests [`7651438`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7651438021ba580f5710f301b27ae5c0fc7a7674)
* **thermal-manager:** add unit tests for the `TestThermalManager` class [`d7f83b8`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d7f83b8249af25172d25e8e7287be063d8aa9077)
* **watcher:** correct unit test `test_partial_scan` [`cf07093`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/cf070939309b6e4f772542046c7bfb2727f450c6)


### Refactoring

* **cluster:** improve the implementation of the thermal, renewable and the short terme storage [`48c3352`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/48c3352a7e1429cdbc74518f4163d93e97262a9e)
* **commands:** refactor the variant commands to use thermal / renewable configurations [`996fb20`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/996fb20d5359ab7f6184ac02945de200f20a294b)
* **commands:** simplify implementation of study variant commands and improve constraints [`4ce9bd0`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4ce9bd039ec31441f0f17860ca0896ddc951f513)
* **commands:** refactor the variant commands to use thermal / renewable configurations [`ff3ccdf`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ff3ccdf4f7721aff8bf1d89e3d265bb4b001f884)
* **config:** create base classes use to configure thermal and renewable clusters and short term storage [`e7e7198`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e7e719869e27cdea7e1b5a87875692af7d4d1977)
* **config:** use `create_st_storage_config` during config parsing [`0d1bac8`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0d1bac80dcead8dc5fe1d0f8276e7905456ae1cb)
* **launcher-service:** rename long variable name `user_who_launched_the_study` [`4ec7cb0`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4ec7cb013be776489f43ccf0c7940d36018cbd7e)
* **login-model:** drop superfluous `__eq__` operator [`73bc168`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/73bc168327594e533ced27c404f67c494bfa0908)
* **raw-study:** the `create_from_fs` method is changed to return a `NamedTuple` (perf) [`191fb98`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/191fb98c0723299d6c6c531cf2a61140c3fd4c1a)
* **role-type:** replace `is_higher_or_equals` by `__ge__` operator [`fc10814`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/fc108147ddc5505c8fcf5833891ade4ec765b940)
* **st-storage:** implement `STStorageProperties` using `BaseClusterProperties` class [`0cc639e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0cc639e1cf3c1aee57d70ff137acc0c479335e82)
* **table-mode:** simplify implementation of the `TableModeManager` class [`52fcb80`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/52fcb80e0e1a8ee7afccc8a79285925b7fbb6fd0)
* **thermal-api:** replace the `DELETE` permission with `WRITE` in the `delete_thermal_clusters` endpoint [`37f99ac`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/37f99ac62a711fd72877799e2aafd0919d960e58)
* **thermal-manager:** correct the `update_cluster` method to update only required and changed properties [`9715add`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9715addf45c412e8b3017852d49e890080c2591b)
* **utils:** replace HTTP exception with `BadArchiveContent` in `extract_zip` function, and update documentation accordingly [`2143dd7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2143dd7cc2fa20b5f6ecdb7395a4f9c2d08e696d)


### Styles

* **api-thermal:** sort imports and reformat source code. [`451c27c`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/451c27cc39a2323dd665297eaf05034b5fd5da4b)
* **model:** simplify typing imports [`2d77d65`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2d77d65f9ac89c788366045fd544202f8dd4c5d3)
* **typing:** replace `IO[bytes]` by `typing.BinaryIO` in function signatures [`4e2e5f9`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4e2e5f92c66f0792d0ea4bea3a1d5e14eb686a03)
* **ui:** update file with new Prettier version [`dfd79a7`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/dfd79a7dd73a5e769a20eaff7b9234e829ab8cf4)
* **ui:** issue with Prettier [`b204b6a`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b204b6acafe5bd03036b078bbc72233366d46b1d)


### Chore

* fix typo in the documentation of shell scripts [`#1793`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1793)
* correct the typing of the `camel_case_model` decorator [`4784a74`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4784a744c84067beba9e1c11d0c33938821524ef)
* correct bad imports in unit tests [`786de74`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/786de74c3606455465fb6204aaf3f310f092de5c)
* fix typing in `CommandExtractor` class [`0da8f3e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0da8f3e12e5e2c7f1eb2e3bdd63257d3cf3d74b0)
* handle all ancestor classes in `AllOptionalMetaclass` [`7153292`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7153292a74aad0f70a4f1a09d85f95fb440acabf)
* correct indentation in docstring [`6d19ebb`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6d19ebb101dc0cbe0d3b2a602e668d562328288c)
* **api:** modify `ThermalConfig` in API example to avoid `ValidationError` [`#1795`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1795)
* **api-thermal:** improve typing of functions [`36ea466`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/36ea466ba75b9c06477cbc4d9a31ddb51ecb168f)
* **doc:** correct image names and titles in the documentation [`b976713`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b9767132389f2ad09b3a6cd57a0870efb9f0eb38)


### Reverts

* change `requirements.txt` to restore `PyYAML~=5.4.1` [`cf47556`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/cf47556e8161bf7f184cac5bc08904954f04b1f6)



v2.15.6 (2023-11-24)
--------------------

### Performance

* **variant:** correct slow variant study snapshot generation [`#1828`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1828)


### Documentation

* **RTD:** correct the configuration for [ReadTheDocs](https://antares-web.readthedocs.io/en/latest/) [`#1833`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1833)


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>.



v2.15.5 (2023-11-16)
--------------------

### Features

*  Remove studies filters and search value from localStorage [`#1788`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1788)
*  **ui-study:** translate generate button in command view [`#1801`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1801)
*  **launcher:** add information about which user launched a study [`#1808`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1808)


### Bug Fixes

*  **tasks:** resolve incorrect UTC timezone usage for task completion dates in list view [`#1786`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1786)
*  **upgrade:** remove tmp files when upgrading [`#1804`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1804)
*  **variant:** generates cascades of variants synchronously to avoid timeout dead locks [`#1806`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1806)


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>



v2.15.4 (2023-10-25)
--------------------

### Tests

*  **commands:** refactored study variant command unit tests, improved coverage, and fixed deprecated attribute usage ([8bd0bdf](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8bd0bdf93c1a9ef0ee12570cb7d398ba7212b2fe))


### Bug Fixes

*  **results-ui:** display results for a specific year [`#1779`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1779)
*  **ui-study:** remove popup to prevent close after variant creation [`#1773`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1773)
*  **raw:** fix HTTP exception when going on debug view [`#1769`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1769)


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>



v2.15.3 (2023-10-12)
--------------------

### Hotfix

* **api-raw:** correct the `/studies/{uuid}/raw` endpoint to return "text/plain" content for matrices [`#1766`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1766)
* **model:** error 500 in cluster list when area change [`0923c5e`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0923c5e990521e1a4543ec7e07ea4cab51d46162)


### Performance

* **storage:** make study_upgrader much faster [`#1533`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1533)



v2.15.2 (2023-10-11)
--------------------

### Hotfix

*  **service:** user connected via tokens cannot create a study [`1757`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1757) ([f620197](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f6201976a653db19739cbc42e91ea27ac790da10))


### Features

*  **binding-constraint:** handling binding constraints frequency in study configuration parsing [`1702`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1702) ([703351a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/703351a6d8d4f70491e66c3c54a92c6d28cb92ea))
   - add the binding constraint series in the matrix constants generator ([e00d58b](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e00d58b203023363860cb0e849576e02ed97fd81))
   - command `create_binding_constraint` can check the matrix shape ([68bf99f](https://github.com/AntaresSimulatorTeam/AntaREST/commit/68bf99f1170181f6111bc15c03ede27030f809d2))
   - command `update_binding_constraint` can check the matrix shape ([c962f73](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c962f7344c7ea07c7a8c7699b2af35f90f3b853c))
   - add missing command docstring ([d277805](https://github.com/AntaresSimulatorTeam/AntaREST/commit/d277805c10d3f9c7134166e6d2f7170c7b752428))
   - reduce code duplication ([b41d957](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b41d957cffa6a8dde21a022f8b6c24c8de2559a2))
   - correct `test_command_factory` unit test to ignore abstract commands ([789c2ad](https://github.com/AntaresSimulatorTeam/AntaREST/commit/789c2adfc3ef3999f3779a345e0730f2f9ad906a))
*  **api:** add endpoint get_nb_cores [`1727`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1727) ([9cfa9f1](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9cfa9f13d363ea4f73aa31ed760d525b091f04a4))
*  **st-storage:** allow all parameters in endpoint for short term storage creation [`1736`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1736) ([853cf6b](https://github.com/AntaresSimulatorTeam/AntaREST/commit/853cf6ba48a23d39f247a0842afac440c4ea4570))


### Chore

*  **sonarcloud:** correct SonarCloud issues ([901d00d](https://github.com/AntaresSimulatorTeam/AntaREST/commit/901d00df558f7e79b728e2ce7406d1bdea69f839))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>



v2.15.1 (2023-10-05)
--------------------

### Features

* **ui-results:** move filters on top of matrices [`#1751`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1751)
* **ui-outputs:** add outputs synthesis view [`#1737`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1737)


### Bug Fixes

* **api:** allow `NaN`, `+Infinity`, and `-Infinity` values in JSON response [`7394248`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7394248821ad5e2e8e5b51d389896c745740225d)
* **ui-xpansion:** display issue in form [`#1754`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1754)
* **raw:** impossible to see matrix containing NaN values [`#1714`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1714)
* **raw:** allow NaN in matrices [`0cad1a9`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0cad1a969fd14e81cf502aecb821df4b2d7abcb6)


### Tests

* **tests:** add a test to ensure GET `/raw` endpoint reads NaN values [`29b1f71`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/29b1f71856463542dcc0170fe97bc6832ec4a72a)



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
* **desktop:** enable year-by-year & synthesis output in study "000 Free Data Sample" [`#1735`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1735)
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

* **github-actions:** update Node.js version to 22.13.0 [`b9988f6`](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b9988f6dedc5a653de00bf5becc917487ce589e6)
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

*  **ui-i18n:** add missing adequacy patch translations [`1680`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1680) ([8a06461](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8a06461f4118227b94be7f587d37ea2430c70505))
*  **ui:** removed the "patch" number from the list of versions in the simulation launch dialog when it's equal to 0 [`1698`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1698) ([1bc0156](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1bc0156c3e08e321e9ccc396b95cadeabf1c1fc7))


### Bug Fixes

*  **web:** modified API response model to prevent Watcher's ValidationError [`1526`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1526) ([b0e48d1](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b0e48d1bd31463cb6ce5e9aefeff761c016d0b35))
*  **xpansion:** corrected field types for Xpansion parameters (sensitivity analysis) ([3e481b9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3e481b9c8866ecc3dc42e351552e1ded036f62ad))
*  **variant:** fixed implementation of the method for extracting the difference between two studies ([c534785](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c5347851da867a19b990e05c6516bedc7508c8ce))
*  **api:** added missing `use_leeway` field and validation rules in the hydro configuration form [`1650`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1650) ([27e46e5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/27e46e5bda77aed65c84e82931d426b4b69a43bd))
*  **export:** ZIP outputs are no longer compressed before export (used by Xpansion) [`1656`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1656) ([cba6261](https://github.com/AntaresSimulatorTeam/AntaREST/commit/cba62613e19712240f74f417854e95bd588ba95d))
*  **log-parser:** simplified analysis and improved accuracy in displaying simulation progress for a study [`1682`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1682) ([2442674](https://github.com/AntaresSimulatorTeam/AntaREST/commit/24426749e9b6100eb3ab4b7159f615444242b95a))
*  **table-mode:** corrected reading of UI information when the study has only one area [`1674`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1674) ([55c4181](https://github.com/AntaresSimulatorTeam/AntaREST/commit/55c4181b64959c5e191fed2256437fc95787199f))
*  **table-mode:** issue to read area information in the case where the study has only one area [`1690`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1690) ([87d9617](https://github.com/AntaresSimulatorTeam/AntaREST/commit/87d961703cebdc037671fe73988903eb14dd9547))
*  **command:** improve INI reader to support API PUT `/v1/studies/{uuid}/raw` [`1461`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1461) ([9e5cf25](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9e5cf25b2f69890016ea36f3be0e9ac03c7695b6))
*  **variant:** fixed time series deletion of renewable clusters [`1693`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1693) ([4ba1b17](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4ba1b17dd3c1b8ea62a5a02f39d15e94a4b9a331))
*  **launcher:** fixing launcher versions display and creation of the endpoint `/v1/launcher/versions` ([410afc2](https://github.com/AntaresSimulatorTeam/AntaREST/commit/410afc2e4ecbb296878985839ee27f84bc70d9d8))
   and [`1672`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1672) ([a76f3a9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a76f3a9f01df0225d7fb54b20ba3ff599d749138))
*  **launcher:** set the default number of cores to 22 (instead of 12) [`1695`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1695) ([2c89799](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2c8979916d46a0ed46a67bc75ac9a2e365e3f164))


### Continuous Integration

* upgrade mypy to v1.4.1 and Black to v23.7.0 for improved typing and formatting [`1685`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1685) ([7cff8c5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7cff8c56c38728a1b29eae0221bcc8226e9ca80c))


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

*  **launcher:** take into account the `nb_cpu` in the local Solver command line [`1603`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1603) ([7bb4f0c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7bb4f0c45db8ddbaedc1a814d0bfddb9fb440aba))
*  **api:** resolve version display issue in Desktop's `/version` endpoint [`1605`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1605) ([a0bf966](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a0bf966dc0b7a0ee302b7d25ff0d95f5307d8117))
*  **study:** fixing case sensitivity issues in reading study configuration [`1610`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1610) ([f03ad59](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f03ad59f41a4d5a29a088e7ff98d20037540563b))
*  **api:** correct `/kill` end-point implementation to work with PyInstaller ([213fb88](https://github.com/AntaresSimulatorTeam/AntaREST/commit/213fb885b05490afe573938ec4300f07b561b2dd))
*  **fastapi:** correct URL inconsistency between the webapp and the API [`1612`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1612) ([195d22c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/195d22c7005e2abad7f389164b0701a8fa24b98c))
*  **i18n:** wrong translations and add missing keys [`1615`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1615) ([7a7019c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7a7019cc1e900feaa5681d2244a81550510e9a78))
*  **deploy:** change example study settings to allow parallel run [`1617`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1617) ([389793e](https://github.com/AntaresSimulatorTeam/AntaREST/commit/389793e08dee0f05dfe68d952e9b85b64b3bc57e))
*  **variant:** get synthesis now also works for level 2+ variants [`1622`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1622) ([661b856](https://github.com/AntaresSimulatorTeam/AntaREST/commit/661b856331673ac792fd2ca264d0fb45433d3ee5))
*  **results:** refresh study outputs when job completed and add back button [`1621`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1621) ([39846c0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/39846c07db0ccd540fcf73fe8a5d711012101226))
*  **deploy:** remove unnecessary Outputs from "000 Free Data Sample" study [`1628`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1628) ([a154dac](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a154dacdc11e99a38cbc2d2930c50875563b76a2))


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
*  **error:** improve error handling with enhanced error message [`1590`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1590) ([9e22aee](https://github.com/AntaresSimulatorTeam/AntaREST/commit/9e22aee25a812b81a323c83a043ffc36f0b1eb46))
*  **matrix:** significant performance enhancement for Time Series update [`1588`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1588) ([220107a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/220107aa2ff18be556960ecf367816cd1aa4ed3f))
*  **launcher:** correct the launching of the local Antares Solver ([8a31514](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8a31514f5995d02e7e23402251396bda2ce22580))
*  **api:** add missing "annual" key on correlation config for new areas [`1600`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1600) ([ac98a76](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ac98a76ca591dc1d582eacd5d00c258bbf06ac5f))


### Documentation

* update user instructions for Antares Web Desktop version ([98bcac5](https://github.com/AntaresSimulatorTeam/AntaREST/commit/98bcac590ba21cae68980172f120627143f090d4))


### Features

*  **common:** display a snackbar error when async default values failed in Form [`1592`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1592) ([c213437](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c213437fc4ac82ac5c1aab4dcdf6638729b81497))


### Contributors

<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/hdinia">hdinia</a>


v2.14.2 (2023-06-12)
--------------------

### Bug Fixes

*  **renewable:** fixing issue with missing display of renewable cluster form [`1545`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1545) ([03c7628](https://github.com/AntaresSimulatorTeam/AntaREST/commit/03c76280a88373ace47121bd44a2fe529bcd7343))
*  **worker:** archive worker must be kept alive for processing [`1567`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1567) ([34e1675](https://github.com/AntaresSimulatorTeam/AntaREST/commit/34e1675737d5af390f4be97b47898ad1e60a7b51))
*  **build:** fix pyinstaller build [`1566`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1566) ([2c7b899](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2c7b89936afb0ebc03d79f9505daa901c1a8a003))
*  **desktop:** correct date parsing in localized environment [`1568`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1568) ([1d9177a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1d9177af66e68983a8db3ca3858449605b24d9f9))
*  **matrix:** check invalid params and empty matrix in matrix update [`1572`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1572) ([f80aa6b](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f80aa6b2178192660d55370977f1495ed1e72f00))
*  **model:** raise an error if the "about-the-study/parameters.ini" file is missing in the ZIP file [`1582`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1582) ([c04d467](https://github.com/AntaresSimulatorTeam/AntaREST/commit/c04d4676aaa7319e308d36d2345fb76d59d3119b))


### Features

*  **matrix:** improve matrix read/write using NumPy [`1562`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1562) ([2784828](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2784828b7f10ff53d2f59ca594525243d97aaa6a))


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
*  **ui:** add @total-typescript/ts-reset lib and tsUtils [`1408`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1408) ([aa5e3e8](https://github.com/AntaresSimulatorTeam/AntaREST/commit/aa5e3e87d95b8b5061030025e89443e1fc71823d))
*  **ui:** update react-hook-form lib and use the new API [`1444`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1444) ([1d129d9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1d129d9d6bac97deee9ebc98d3334117fe837444))


### Bug Fixes

*  **common:** field array change doesn't trigger on auto submit [`1439`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1439) ([910db64](https://github.com/AntaresSimulatorTeam/AntaREST/commit/910db64ca872468a1f01ced99083962022daa05c))
*  **matrix:** correct the frequency of some matrices [`1384`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1384) ([2644416](https://github.com/AntaresSimulatorTeam/AntaREST/commit/26444169b9ab60f54e8ee7a2d16fb10dbc4d537e))
*  **ui-common:** add matrices float handling ([99ba81f](https://github.com/AntaresSimulatorTeam/AntaREST/commit/99ba81fce26bbd99340990d0207761463558d4a7))
*  **ui-hydro:** correct column names ([e529a79](https://github.com/AntaresSimulatorTeam/AntaREST/commit/e529a799071e9c5485e2cba35eb5a7c2c18c25e7))
*  **ui-hydro:** update hydro matrices columns ([56641d7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/56641d7ad995d8b7dd6755b13f1689b32b6296d8))
*  **ui:** fix typo on error page [`1390`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1390) ([da00131](https://github.com/AntaresSimulatorTeam/AntaREST/commit/da0013190d7e31e1afe9d8f5c3b03c378ca41507))
*  **ui:** size issue with HandsonTable ([f63edda](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f63edda65345bf9848fb44a8a067a885ca5fbd83))


### Styles

*  **api-tablemode:** fix typo ([5e5e4e7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/5e5e4e7efcfc93e4682825a9c514417679fba89b))
*  **ui:** fix filename ([ad9f9c0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/ad9f9c055713ef81a94b8c7bb01caae783ab8de9))


### Documentation

*  **api:** add API documentation for the hydraulic allocation (and fix minor awkwardness) ([08680af](https://github.com/AntaresSimulatorTeam/AntaREST/commit/08680af4344b7dd9aa365267a0deb8d9094f0294))
*  **study-upgrade:** add the "How to upgrade a study?" topic in the documentation [`1400`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1400) ([2d03bef](https://github.com/AntaresSimulatorTeam/AntaREST/commit/2d03befe999e558c989e1cce1f51186beff5502b))

> IMPORTANT: The `antares-launcher` Git submodule is dropped.


### Contributors

<a href="https://github.com/hdinia">hdinia</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/flomnes">flomnes</a>,
<a href="https://github.com/laurent-laporte-pro">laurent-laporte-pro</a>


v2.13.2 (2023-04-25)
--------------------

### Bug Fixes

*  **api:** fix uncaught exceptions stopping slurm launcher loop [`1477`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1477) ([2737914](https://github.com/AntaresSimulatorTeam/AntaREST/commit/27379146cfa12cc90e38f2f0d77009d80f3164db))

### Contributors

<a href="https://github.com/sylvlecl">Sylvain LECLERC</a>

v2.13.1 (2023-04-11)
--------------------

### Bug Fixes

*  **desktop:** use Antares Solver v8.5 for Antares Web Desktop version [`1414`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1414) ([6979e87](https://github.com/AntaresSimulatorTeam/AntaREST/commit/6979e871dac39a34e76fe6a72b2ccf4502e8a288))
*  **launcher:** improved reliability of task state retrieval sent to SLUM [`1417`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1417) ([101dd8c](https://github.com/AntaresSimulatorTeam/AntaREST/commit/101dd8c2a149c5112669d557d0851a9b1659d683))
*  **api:** show Antares Launcher version in the `/version` end point [`1415`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1415) ([12bfa84](https://github.com/AntaresSimulatorTeam/AntaREST/commit/12bfa849e2232ea275851ad11407faf70bb91d2c))
*  **desktop:** use Antares Solver v8.5.0 for Antares Web Desktop version [`1419`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1419) ([8f55667](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8f55667b52eea39a7d0e646811f16ef024afbbe0))
*  **api:** better handling of exception to catch the stacktrace [`1422`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1422) ([a2d0de0](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a2d0de073582070282131b3bcd346e6fbe7315ab))


### Contributors

<a href="https://github.com/laurent-laporte-pro">Laurent LAPORTE</a>, and
<a href="https://github.com/MartinBelthle">MartinBelthle</a>


v2.13.0 (2023-03-09)
--------------------

### Features

*  **ui-common:** add doc link on subsections [`1241`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1241) ([1331232](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1331232e418ebfbf3cc1a82725b95cb11cf8b9bc))
*  **api-websocket:** better handle the events in eventbus braodcasting [`1240`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1240) ([99f2590](https://github.com/AntaresSimulatorTeam/AntaREST/commit/99f25906559f782bcad857650f1b8ebfcfe584c8))
*  **ui-commands:** add confirm dialog on delete command [`1258`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1258) ([0be70f8](https://github.com/AntaresSimulatorTeam/AntaREST/commit/0be70f87ec03c491faf1d29c8d78b29615d1da9a))
*  **redux:** extend left menu by default [`1266`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1266) ([1c042af](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1c042af7d4c713bcbd530062cb9e31ead45e1517))
*  **ui-study:** add text ellipsis on study name [`1270`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1270) ([6938114](https://github.com/AntaresSimulatorTeam/AntaREST/commit/69381145ab1e4224e874a59dcec2297dae951b51))
*  **launcher:** integrate Antares Solver v8.5.0. [`1282`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1282) ([57bbd3d](https://github.com/AntaresSimulatorTeam/AntaREST/commit/57bbd3d0974b104dc4b58f0f1756e40f50b2189f))
*  **ui:** add tooltips to folded menu [`1279`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1279) ([b489dd9](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b489dd9db8e5d5b3a8ab6a29721d292d3841dcce))
*  **github:** add feature request template [`1284`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1284) ([73aa920](https://github.com/AntaresSimulatorTeam/AntaREST/commit/73aa920fa15d5a3397d49e00319acf808678d021))
*  **github:** add bug report template  [`1283`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1283) ([8e05370](https://github.com/AntaresSimulatorTeam/AntaREST/commit/8e05370c5b1ba212545515984eb379c7a7fe6f9d))
*  **ui-results:** add download button on results matrix [`1290`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1290) ([343df96](https://github.com/AntaresSimulatorTeam/AntaREST/commit/343df968fec3dc6658f1e41040bc656cd80a104c))
*  **ui-redux:** add menu state in local storage [`1297`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1297) ([3160f29](https://github.com/AntaresSimulatorTeam/AntaREST/commit/3160f295ffd06312f2a77ec0ea2dd7da0c04fbed))
*  **ui-study:** add path tooltip on study title [`1300`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1300) ([429d288](https://github.com/AntaresSimulatorTeam/AntaREST/commit/429d288ce5aa96c0c65724647b211639b4153417))
*  **ui-map:** add layers and districts French translations [`1292`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1292) ([12f4e92](https://github.com/AntaresSimulatorTeam/AntaREST/commit/12f4e9235d5cd2256a52d9e31ec440c0756272b4))


### Code Refactoring

* simplify the maintenance mode and service. ([1590f84](https://github.com/AntaresSimulatorTeam/AntaREST/commit/1590f840dbec5ca4fcd1eba2c125de3e4f40ebef))
* change the `MaintenanceMode` class to implement a conversion from/to `bool`. ([a5a5689](https://github.com/AntaresSimulatorTeam/AntaREST/commit/a5a568984c9562e3eba67ba30c0a076b8f30190e))


### Bug Fixes

*  **api-workers:** Prevent scanning of the default workspace [`1244`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1244) ([06fd2bc](https://github.com/AntaresSimulatorTeam/AntaREST/commit/06fd2bca478fc4f579ba0760e37969038e560f97))
*  **ui-study:** remove the create command button [`1251`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1251) ([463e7a7](https://github.com/AntaresSimulatorTeam/AntaREST/commit/463e7a789eebd2b28c33bd18e833bbd30dc9268a))
*  **ui-wording:** correct wording of user messages [`1271`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1271) ([7f66c1a](https://github.com/AntaresSimulatorTeam/AntaREST/commit/7f66c1aa518bea09c2db52ae87ef36e14cd5b9e0))
*  **ui-wording:** correct french translations [`1273`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1273) ([f4f62f2](https://github.com/AntaresSimulatorTeam/AntaREST/commit/f4f62f252d8b5556ba1cb2b6027360b9066327e0))
*  **api:** correct the way the task completion is notified to the event bus [`1301`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1301) ([b9cea1e](https://github.com/AntaresSimulatorTeam/AntaREST/commit/b9cea1ebd644869a459cbf002661c4a833389cb2))
*  **storage:** ignore zipped output if an unzipped version exists [`1269`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1269) ([032b581](https://github.com/AntaresSimulatorTeam/AntaREST/commit/032b58134a4e2e9da50848d6de438d23a0f00086))


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

* remove Create Issue Branch app file [`1299`](https://github.com/AntaresSimulatorTeam/AntaREST/pull/1299) ([4e81fa6](https://github.com/AntaresSimulatorTeam/AntaREST/commit/4e81fa646552a58d56984171c644104d4dd79ab7))


### Contributors

<a href="https://github.com/hdinia">hdinia</a>,
<a href="https://github.com/laurent-laporte-pro">Laurent LAPORTE</a>,
<a href="https://github.com/pl-buiquang">pl-buiquang</a>,
<a href="https://github.com/skamril">skamril</a>,
<a href="https://github.com/MartinBelthle">MartinBelthle</a>
