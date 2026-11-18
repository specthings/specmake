<!--
SPDX-License-Identifier: CC-BY-SA-4.0

Copyright (C) 2026 embedded brains GmbH & Co. KG
-->
# AGENTS.md

## Build and test

Run `make` before a commit. It regenerates `src/specmake/spec.pickle`, formats,
analyses `src/` and runs the tests in parallel. CI runs `make` and fails on any
diff which it leaves in the tree.

The tests need `git` with a configured user name and e-mail address, and
`unifdef`.

`pyproject.toml` makes `pytest` fail below 100 % line and branch coverage. Run
a single test with `--no-cov`:

```
uv run pytest --no-cov tests/test_elf.py::test_loadable_digest_covers_loaded_parts
```

Git tracks two pickles of types:

| File | Source | Regenerate with |
| ---- | ------ | --------------- |
| `src/specmake/spec.pickle` | `spec-types/spec/` | `make` |
| `tests/spec.pickle` | `tests/spec-types/spec/` | `uv run specpickle tests/spec-types tests/spec.pickle` |

`make analyse` runs `reuse lint`. A new file needs an SPDX header or an entry
in `REUSE.toml`. Enclose license identifiers which a file holds as data in
`REUSE-IgnoreStart` and `REUSE-IgnoreEnd` comments.

## Architecture

specmake builds a package from items of
[specitems](https://github.com/specthings/specitems). It uses the types of
[specware](https://github.com/specthings/specware) and runs tests through
[spectestrunner](https://github.com/specthings/spectestrunner).

- The `pkg/...` items of a package describe its build steps. Their types live
  in `spec-types/spec/`. The entry point `specitems_type_provider.plugins`
  hands them to specitems.
- `create_build_item_factory()` in `pkgfactory.py` maps each item type to a
  `BuildItem` class. Add a new step type there.
- `PackageBuildDirector` in `pkgitems.py` runs the build. A link to an input
  stores the `hash` of that input. `BuildItem.build()` runs a step only if a
  hash differs or the build is forced.
- `DirectoryStateBase` in `dirstatebase.py` is the base of a step which
  produces files. It records the files and their digests.
- The `*builder.py` modules generate the documents of a package with Sphinx.

## Tests

`tests/spec-*/` holds the fixture packages. `tests/test-files/` is the default
workspace of a package build.

## Commits

A commit message follows Conventional Commits with a sentence-case subject. The
scope is the module name, or `spec` for `spec-types/`. Add the `Assisted-by:`
and `Signed-off-by:` trailers as `CONTRIBUTING.md` prescribes. Run
`make commitlint` before a push. Only a maintainer runs `make publish` or
`make devel-publish`.
