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
    assert "BUILD_JOBS=12" in arguments
    assert f"OUTPUT_UID={os.getuid()}" in arguments
    assert "gosu docker make -C release/src-rt-5.02hnd rt-ac86u" in "\n".join(arguments)
    assert "gosu docker git checkout --detach" in "\n".join(arguments)
    assert "rsync -a /project/.git/ /build/source/.git/" in "\n".join(arguments)
    assert "chown -R docker:docker /build/source/.git" in "\n".join(arguments)
    assert "chown -R docker:docker /build/source\n    fi" in "\n".join(arguments)
    assert f"type=volume,source=asuswrt-ac86u-{revision},destination=/build" in arguments
    assert f"type=bind,source={root},destination=/project,readonly" in arguments
    assert "gnuton/asuswrt-merlin-toolchains-docker@sha256:8c9681987352d6eb8a38708126c9c39edd8dd28a7bf6c0cedc0e9534387f9ab3" in arguments
    assert subprocess.run(["bash", "tools/build-rt-ac86u", "missing-build-revision"], cwd=root, env=environment, capture_output=True).returncode != 0
    for jobs in ("0", "invalid", "-1"):
        assert subprocess.run(["bash", "tools/build-rt-ac86u", "386.14_2"], cwd=root, env=dict(environment, BUILD_JOBS=jobs), capture_output=True).returncode != 0
    subprocess.run(["bash", "tools/build-rt-ac86u", "386.14_2"], cwd=root, env=dict(environment, BUILD_JOBS="4"), check=True)
    assert "BUILD_JOBS=4" in (temporary / "args").read_text().splitlines()

kernel_makefile = (root / "release/src-rt-5.02hnd/kernel/linux-4.1/Makefile").read_text().splitlines()
include_line = kernel_makefile.index("include ../../.config")
with tempfile.TemporaryDirectory() as directory:
    kernel = Path(directory) / "hnd/kernel/linux-4.1"
    kernel.mkdir(parents=True)
    config = kernel.parents[1] / ".config"
    config.write_text("BUILD_NAME = RT-AC86U\n")
    implicit_rule = "\n%.config: FORCE\n\t@touch merge_config_called\nFORCE:\n\t@:\nall:\n\t@true\n"
    (kernel / "Makefile").write_text(kernel_makefile[include_line] + implicit_rule)
    subprocess.run(["make", "all"], cwd=kernel, check=True)
    assert (kernel / "merge_config_called").exists()
    (kernel / "merge_config_called").unlink()
    (kernel / "Makefile").write_text("\n".join(kernel_makefile[include_line:include_line + 2]) + implicit_rule)
    subprocess.run(["make", "all"], cwd=kernel, check=True)
    assert not (kernel / "merge_config_called").exists()
    config.unlink()
    assert subprocess.run(["make", "all"], cwd=kernel, capture_output=True).returncode != 0
print("Build launcher checks passed")
