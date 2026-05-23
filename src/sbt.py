#!/usr/bin/env python3
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

app = typer.Typer()


@app.command()
def sync(srcdir: str, dstdir: str, full: bool = False):
    src = Path(srcdir)
    if not src.is_dir():
        typer.echo(f"Error: source directory '{srcdir}' does not exist.", err=True)
        raise typer.Exit(1)

    dst = Path(dstdir) / src.name
    try:
        dst.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        typer.echo(f"Error: cannot create '{dstdir}' — permission denied.", err=True)
        raise typer.Exit(1)

    snapshot = dst / f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    prior = None
    if not full:
        candidates = sorted(dst.glob("backup-*"))
        if candidates:
            prior = candidates[-1]

    cmd = ["rsync", "-avh"]
    if prior:
        typer.echo(f"🌙 Execute Incremental Backup on {prior.name}")
        cmd.append(f"--link-dest={prior}")
    else:
        typer.echo("🌕 Execute Full Backup")

    cmd += [str(src) + "/", str(snapshot)]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise typer.Exit(1)


@app.command()
def iso(srcdir: str, dstdir: str, volname: Optional[str] = None, pubname: Optional[str] = None):
    src = Path(srcdir)
    dst = Path(dstdir)

    if not src.is_dir():
        typer.echo(f"Error: source directory '{srcdir}' does not exist.", err=True)
        raise typer.Exit(1)

    vol = volname or src.name.upper()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", vol):
        typer.echo(f"Error: volume name '{vol}' must be 1-32 characters of A-Z, a-z, 0-9, _ or -.", err=True)
        raise typer.Exit(1)

    try:
        dst.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        typer.echo(f"Error: cannot create '{dst}' — permission denied. Check the path exists and is writable (WSL drive paths are case-sensitive, e.g. /mnt/e not /mnt/E).", err=True)
        raise typer.Exit(1)

    iso_path = dst / f"{vol}.iso"
    if iso_path.exists():
        typer.echo(f"Error: '{iso_path}' already exists.", err=True)
        raise typer.Exit(1)

    cmd = [
        "mkisofs",
        "-J",       # Joliet: Windows-compatible long filenames
        "-r",       # Rock Ridge: preserve Unix file attributes and symlinks
        "-U",       # allow untranslated filenames up to 31 characters
        "-D",       # disable deep directory relocation
        "-V", vol,  # volume label
    ]
    if pubname:
        cmd += ["-P", pubname]  # publisher name embedded in the ISO header
    cmd += ["-o", str(iso_path), str(src)]

    typer.echo(f"💿 Creating ISO '{vol}' from '{src}' → '{iso_path}'")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
