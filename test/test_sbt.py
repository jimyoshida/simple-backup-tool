from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from sbt import app

runner = CliRunner()


def make_result(returncode=0):
    r = MagicMock()
    r.returncode = returncode
    return r


# ---------------------------------------------------------------------------
# sync — input validation
# ---------------------------------------------------------------------------

def test_sync_missing_srcdir(tmp_path):
    result = runner.invoke(app, ["sync", str(tmp_path / "nope"), str(tmp_path / "dst")])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_sync_srcdir_is_file(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    result = runner.invoke(app, ["sync", str(f), str(tmp_path / "dst")])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_sync_dstdir_permission_denied(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.Path.mkdir", side_effect=PermissionError):
        result = runner.invoke(app, ["sync", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 1
    assert "permission denied" in result.output


# ---------------------------------------------------------------------------
# sync — full vs incremental selection
# ---------------------------------------------------------------------------

def test_sync_full_backup_when_no_prior(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        result = runner.invoke(app, ["sync", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert "--link-dest" not in " ".join(cmd)
    assert "Full Backup" in result.output


def test_sync_incremental_backup_when_prior_exists(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_base = tmp_path / "dst" / "src"
    prior = dst_base / "backup-20260101-120000"
    prior.mkdir(parents=True)

    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        result = runner.invoke(app, ["sync", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert any("--link-dest" in arg for arg in cmd)
    assert str(prior) in " ".join(cmd)
    assert "Incremental Backup" in result.output


def test_sync_incremental_uses_latest_prior(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_base = tmp_path / "dst" / "src"
    older = dst_base / "backup-20260101-120000"
    newer = dst_base / "backup-20260201-120000"
    older.mkdir(parents=True)
    newer.mkdir(parents=True)

    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["sync", str(src), str(tmp_path / "dst")])
    cmd = mock_run.call_args[0][0]
    assert str(newer) in " ".join(cmd)
    assert str(older) not in " ".join(cmd)


def test_sync_full_flag_overrides_prior(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst_base = tmp_path / "dst" / "src"
    prior = dst_base / "backup-20260101-120000"
    prior.mkdir(parents=True)

    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        result = runner.invoke(app, ["sync", "--full", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 0
    cmd = mock_run.call_args[0][0]
    assert "--link-dest" not in " ".join(cmd)
    assert "Full Backup" in result.output


# ---------------------------------------------------------------------------
# sync — rsync command construction
# ---------------------------------------------------------------------------

def test_sync_rsync_command_shape(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["sync", str(src), str(tmp_path / "dst")])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "rsync"
    assert "-avh" in cmd
    # src path must have a trailing slash
    assert any(arg == str(src) + "/" for arg in cmd)


def test_sync_rsync_failure_exits_1(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result(returncode=1)):
        result = runner.invoke(app, ["sync", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# iso — volume name validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("volname", [
    "DOCS",
    "my-backup",
    "data_2026",
    "A" * 32,          # exactly 32 chars — boundary
    "Mix-ed_123",
])
def test_iso_valid_volname(tmp_path, volname):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()):
        result = runner.invoke(app, ["iso", str(src), str(tmp_path / "dst"), "--volname", volname])
    assert result.exit_code == 0


@pytest.mark.parametrize("volname", [
    "A" * 33,           # 33 chars — one over the limit
    "has space",
    "has.dot",
    "has/slash",
    "has@at",
])
def test_iso_invalid_volname(tmp_path, volname):
    src = tmp_path / "src"
    src.mkdir()
    result = runner.invoke(app, ["iso", str(src), str(tmp_path / "dst"), "--volname", volname])
    assert result.exit_code == 1
    assert "volume name" in result.output


def test_iso_default_volname_is_srcdir_uppercased(tmp_path):
    src = tmp_path / "mydata"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["iso", str(src), str(tmp_path / "dst")])
    cmd = mock_run.call_args[0][0]
    assert "MYDATA" in cmd


# ---------------------------------------------------------------------------
# iso — ISO file already exists guard
# ---------------------------------------------------------------------------

def test_iso_refuses_if_output_already_exists(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    dst.mkdir()
    (dst / "SRC.iso").write_bytes(b"")   # pre-existing file
    result = runner.invoke(app, ["iso", str(src), str(dst)])
    assert result.exit_code == 1
    assert "already exists" in result.output


# ---------------------------------------------------------------------------
# iso — mkisofs command construction
# ---------------------------------------------------------------------------

def test_iso_mkisofs_base_flags(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["iso", str(src), str(tmp_path / "dst"), "--volname", "TEST"])
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "mkisofs"
    for flag in ["-J", "-r", "-U", "-D"]:
        assert flag in cmd
    assert "-V" in cmd
    assert cmd[cmd.index("-V") + 1] == "TEST"


def test_iso_mkisofs_output_path(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    dst = tmp_path / "dst"
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["iso", str(src), str(dst), "--volname", "VOL"])
    cmd = mock_run.call_args[0][0]
    assert "-o" in cmd
    assert cmd[cmd.index("-o") + 1] == str(dst / "VOL.iso")
    assert cmd[-1] == str(src)


def test_iso_pubname_included_when_provided(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["iso", str(src), str(tmp_path / "dst"), "--pubname", "ACME Corp"])
    cmd = mock_run.call_args[0][0]
    assert "-P" in cmd
    assert cmd[cmd.index("-P") + 1] == "ACME Corp"


def test_iso_pubname_absent_when_not_provided(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result()) as mock_run:
        runner.invoke(app, ["iso", str(src), str(tmp_path / "dst")])
    cmd = mock_run.call_args[0][0]
    assert "-P" not in cmd


def test_iso_mkisofs_failure_exits_1(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.subprocess.run", return_value=make_result(returncode=1)):
        result = runner.invoke(app, ["iso", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 1


# ---------------------------------------------------------------------------
# iso — input validation
# ---------------------------------------------------------------------------

def test_iso_missing_srcdir(tmp_path):
    result = runner.invoke(app, ["iso", str(tmp_path / "nope"), str(tmp_path / "dst")])
    assert result.exit_code == 1
    assert "does not exist" in result.output


def test_iso_dstdir_permission_denied(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    with patch("sbt.Path.mkdir", side_effect=PermissionError):
        result = runner.invoke(app, ["iso", str(src), str(tmp_path / "dst")])
    assert result.exit_code == 1
    assert "permission denied" in result.output
