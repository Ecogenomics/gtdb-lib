# [1.9.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.8.0...v1.9.0) (2023-03-03)


### Features

* added run_bash() to execute.py as this can be useful for complicated shell commands ([a87761e](https://github.com/Ecogenomics/gtdb-lib/commit/a87761e8c7e8de68e419d6b49a2e8af2e57a3063))

# [1.8.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.7.0...v1.8.0) (2023-01-12)


### Features

* moved over BioLib functionality required by the GTDB Species Cluster pipeline; predominately extensions to handle Greengenes-style taxonomy strings ([df9e1fe](https://github.com/Ecogenomics/gtdb-lib/commit/df9e1fea09216680748dbb52f1989abcb1a74489))

# [1.7.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.6.0...v1.7.0) (2023-01-07)


### Features

* added execute.py and method for checking accession versions in accession.py. ([eb7bd16](https://github.com/Ecogenomics/gtdb-lib/commit/eb7bd1619c15c36e8a9f26b880a8e391f03b3992))

# [1.6.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.5.0...v1.6.0) (2022-12-19)


### Bug Fixes

* **bootstrap_merge:** Fix a bug where taxa labels would be replaced each iteration. ([a500f4e](https://github.com/Ecogenomics/gtdb-lib/commit/a500f4e53d07b9d94811de70f7522b33810e0d37))
* **cli:** Update bootstrap_merge method to contain CPU argument. ([7f53d98](https://github.com/Ecogenomics/gtdb-lib/commit/7f53d98d333611f65275001e8f9ff81d31d807c1))
* **cli:** Update bootstrap_merge method to contain CPU argument. ([17bd594](https://github.com/Ecogenomics/gtdb-lib/commit/17bd594cb752ae233bee9a04e1539d7264a40d79))


### Features

* **bootstrap_merge:** Updated to multiprocess on individual trees, not across multiple trees. ([2c6046a](https://github.com/Ecogenomics/gtdb-lib/commit/2c6046abdab7c0f37763606e2cc6b90e34dd55ce))
* **convert_accession:** Add CLI and method to convert accessions within a tree to canonical form. ([504154f](https://github.com/Ecogenomics/gtdb-lib/commit/504154fb90632111e228d5e2a76855ecc56a76b0))

# [1.5.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.4.0...v1.5.0) (2022-12-15)


### Bug Fixes

* **typer:** Fix minimum version of Typer for rich support. ([afa2000](https://github.com/Ecogenomics/gtdb-lib/commit/afa2000dbea305406d85ca30419ed94dafeb2b1b))


### Features

* **bootstrap_merge:** Improve performance of method by 30% using numpy. ([cb1b03d](https://github.com/Ecogenomics/gtdb-lib/commit/cb1b03d826e66d63ba923378e1f8c67b7cacd771))
* **bootstrap_merge:** Improve performance of method by 33% using numpy. ([c0d0265](https://github.com/Ecogenomics/gtdb-lib/commit/c0d0265eed8a0b60051a0ce7a1601371cb300f2b))
* **bootstrap_merge:** Improve performance of method by 33% using numpy. ([b24b3dc](https://github.com/Ecogenomics/gtdb-lib/commit/b24b3dcd653a78fb227e862b7ade9ff379bd79b6))

# [1.4.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.3.0...v1.4.0) (2022-12-13)


### Bug Fixes

* **cli:** Add CLI entrypoint to setup.py ([5d471bc](https://github.com/Ecogenomics/gtdb-lib/commit/5d471bc06adcc3f8348b6c3c731a29c67fc81aa0))


### Features

* **bootstrap_merge:** Add multiprocessing option. ([4aea129](https://github.com/Ecogenomics/gtdb-lib/commit/4aea12906b5df2ed00261aa1f61ba1cc21019dd4))

# [1.3.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.2.0...v1.3.0) (2022-12-13)


### Features

* **cli:** Add CLI and tree manipulation methods. ([298954e](https://github.com/Ecogenomics/gtdb-lib/commit/298954e627931b11305b175dae323978b0c287ef))
* **cli:** Add CLI and tree manipulation methods. ([263c2dd](https://github.com/Ecogenomics/gtdb-lib/commit/263c2ddf8c756492921b4eacfc56c5079b39a0a0))
* **cli:** Add CLI and tree manipulation methods. ([f7c04a1](https://github.com/Ecogenomics/gtdb-lib/commit/f7c04a1210a5adc80c1d0fb31ebc110d1e51c547))

# [1.2.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.1.1...v1.2.0) (2022-11-02)


### Features

* **change checksum to filemgmt:** doc refactoring ([25e9042](https://github.com/Ecogenomics/gtdb-lib/commit/25e90426a9640392fd7d5bb533e2614ccdc1c2cf))

## [1.1.1](https://github.com/Ecogenomics/gtdb-lib/compare/v1.1.0...v1.1.1) (2022-10-21)


### Bug Fixes

* **ci:** Fix an issue where version was not being applied to PyPI package. ([6e4add8](https://github.com/Ecogenomics/gtdb-lib/commit/6e4add8b60892db9faf44887e9e65d74a8892f2d))

# [1.1.0](https://github.com/Ecogenomics/gtdb-lib/compare/v1.0.1...v1.1.0) (2022-10-21)


### Features

* **docs/taxon:** Add docs and an example of taxon/taxonomy. ([a010c48](https://github.com/Ecogenomics/gtdb-lib/commit/a010c48113f841c03913468a4c8120d4d756e0a1))
* **iTOL:** File wrappers for iTOL. ([43bd118](https://github.com/Ecogenomics/gtdb-lib/commit/43bd118f088b8a5744890e8d9afcc789104e38ad))
* **iTOL:** File wrappers for iTOL. ([92740b4](https://github.com/Ecogenomics/gtdb-lib/commit/92740b4617ceeed964518d4e688eb0a5eea9d7aa))
* **Tools implementation:** Add first set of tools ([9cc2464](https://github.com/Ecogenomics/gtdb-lib/commit/9cc246487061663401d0518541056192ca288778))

## [1.0.1](https://github.com/Ecogenomics/gtdb-lib/compare/v1.0.0...v1.0.1) (2022-10-07)


### Bug Fixes

* **license:** Incorrect PyPI license. ([9cc7c24](https://github.com/Ecogenomics/gtdb-lib/commit/9cc7c24b4cf18d163084f111453a6a189bde950c))

# 1.0.0 (2022-10-07)


### Features

* **init:** Initial commit. ([9fd9291](https://github.com/Ecogenomics/gtdb-lib/commit/9fd92919af40020064324797b613c971ed6fb10d))
