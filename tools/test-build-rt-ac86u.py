import os
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
revision = subprocess.check_output(["git", "rev-parse", "386.14_2^{commit}"], cwd=root, text=True).strip()
with tempfile.TemporaryDirectory() as directory:
    temporary = Path(directory)
    docker = temporary / "docker"
    docker.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$BUILD_CHECK_ARGS"\n')
    docker.chmod(0o755)
    environment = dict(os.environ, PATH=f"{temporary}:{os.environ['PATH']}", BUILD_CHECK_ARGS=str(temporary / "args"))
    subprocess.run(["bash", "tools/build-rt-ac86u", "386.14_2"], cwd=root, env=environment, check=True)
    arguments = (temporary / "args").read_text().splitlines()
    assert "linux/amd64" in arguments
    assert f"SOURCE_REVISION={revision}" in arguments
    assert f"type=volume,source=asuswrt-ac86u-{revision},destination=/build" in arguments
    assert "gnuton/asuswrt-merlin-toolchains-docker@sha256:8c9681987352d6eb8a38708126c9c39edd8dd28a7bf6c0cedc0e9534387f9ab3" in arguments
    assert subprocess.run(["bash", "tools/build-rt-ac86u", "missing-build-revision"], cwd=root, env=environment, capture_output=True).returncode != 0
print("Build launcher checks passed")
