# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`sbt` (Simple Backup Tool) is a Python 3 CLI utility that wraps `rsync` and `mkisofs` to provide backup operations. It is distributed as a Debian `.deb` package.

## Commands

```bash
# Build
make          # Build the .deb package → out/sbt_1.0.0-1_all.deb
make install  # Install via dpkg (requires sudo)
make uninstall # Remove installed package
make clean    # Remove out/ and tmp/ build artifacts

# Tests
pytest                        # Run all tests
pytest test/test_sbt.py::test_sync_full_backup_when_no_prior  # Run a single test
```

## Layout

```
src/sbt.py        # Entire application (~90 lines)
test/test_sbt.py  # pytest suite
doc/sbt.1         # Unix man page
DEBIAN/control    # Package metadata (version, deps)
build-deb.sh      # Assembles tmp/ structure and calls dpkg-deb
pytest.ini        # Sets testpaths=test, pythonpath=src
```

## Architecture

The entire application is `src/sbt.py`. It uses [Typer](https://typer.tiangolo.com/) to expose two commands, both invoked via `subprocess.run()`; non-zero exit codes raise `typer.Exit(1)`.

- **`sbt sync <srcdir> <dstdir>`** — incremental/full directory backups using `rsync`. Snapshots land at `<dstdir>/<srcdir-basename>/backup-YYYYMMDD-HHMMSS`. Incremental backups use rsync's `--link-dest` pointed at the lexicographically latest prior snapshot; `--full` skips this.
- **`sbt iso <srcdir> <dstdir>`** — creates an ISO 9660 image via `mkisofs` (from the `genisoimage` package). Output is `<dstdir>/<VOLNAME>.iso`. Joliet (`-J`) and Rock Ridge (`-r`) extensions are always enabled. `--volname` defaults to the source directory name uppercased; must match `[A-Za-z0-9_-]{1,32}`. `--pubname` sets the publisher string in the image header.

## Packaging

`build-deb.sh` copies `src/sbt.py` → `tmp/usr/local/bin/sbt` (executable), gzips `doc/sbt.1` into the man path, and runs `dpkg-deb`. The version is read directly from `DEBIAN/control` by the Makefile. To release a new version, bump `Version:` in `DEBIAN/control`.
