# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `asyncio` + `websockets` example.

### Fixed

- Ensure that `subscribe()` receives an empty dictionary of `variables`, even if the client did not include it in the payload.

## [0.1.0] - 2019-13-07

### Added

- `GraphQLWSProtocol` class.
- Integration tests for `asyncio`.

Project-related additions:

- Package setup.
- Changelog.
- Contributing guide.
- README and documentation.

[unreleased]: https://github.com/florimondmanca/subscriptions-transport-ws-python/compare/0.1.0...HEAD
[0.1.0]: https://github.com/florimondmanca/subscriptions-transport-ws-python/compare/21655bd67577617fba051b5d3126e1216b0a2958...0.1.0
