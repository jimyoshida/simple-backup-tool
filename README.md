# sbt (simple backup tool)

A free, CLI-based basic feature alternative to:

- **[AnyToISO](https://crystalidea.com/anytoiso)** (GUI; free for small folders, paid for large) — use `sbt iso` to convert folders to ISO images
- **[AOMEI Backupper](https://www.aomeitech.com/ab/)** (freeware GUI) — use `sbt sync` for incremental directory backups

See also `DEBIAN/control`.

## System Requirements

**Runtime** (automatically installed as `.deb` dependencies):

* Ubuntu 24.04+ (including WSL)
* `rsync`
* `genisoimage` (provides `mkisofs`)
* `python3-typer`

**Development** (package names for `apt`):

* Ubuntu 24.04+ (including WSL)
* `make` (GNU Make)
* `dpkg` (provides `dpkg-deb`)
* `python3-pytest`

## Development

Install Python dependencies (typer and its transitive deps) before running or testing the code:

```bash
pip install -r requirements.txt
```

Run `make test` to execute the pytest suite.

### Build

Run `make` to generate the deb package at `out/sbt_<version>_all.deb`, where `<version>` reflects the value in `DEBIAN/control`.

> **Limitation:** the version is fixed at `1.0.0-1` and not incremented between releases.

### Install

Run `sudo make install` to install the package.

### Uninstall

Run `sudo make uninstall` to remove the package.

## Using Windows drives from WSL

Windows drives are mounted at `/mnt/<letter>` (e.g. `/mnt/d`, `/mnt/e`). C: is auto-mounted by WSL; other drives may need to be mounted manually or added to `/etc/fstab`:

```bash
# Mount a drive for the current session (uid/gid=1000 gives your user ownership)
sudo mkdir -p /mnt/e && sudo mount -t drvfs E: /mnt/e -o uid=1000,gid=1000

# Make it persist across WSL restarts — add to /etc/fstab
echo 'E: /mnt/e drvfs defaults,uid=1000,gid=1000 0 0' | sudo tee -a /etc/fstab
```

Without `uid=1000,gid=1000` the mount is owned by root and `mkdir` will raise a `PermissionError`.

If a drive shows "No such device" despite appearing in `mount`, remount it:

```bash
sudo mount -o remount,uid=1000,gid=1000 /mnt/d
```

`mount-windows-drives.sh` in this repo automates the above — it mounts any number of drives with the invoking user's uid/gid, using `remount` when already mounted to preserve WSL's automount tracking:

```bash
sudo ./mount-windows-drives.sh D E
```
