# RT-AC86U build

Personal fork of [Asuswrt-Merlin](https://github.com/RMerl/asuswrt-merlin.ng), based on tag `386.14_2`, commit `6a5df61aab6f3fa2dffc518994d42e4f2a27fb2b`.

Firmware behavior is unchanged. The `rt-ac86u` branch adds a pinned container build for this model. It does not enable UniFi adoption or add security fixes beyond upstream 386.14_2.

## Build

Install and start Docker, then run from this repository:

```sh
bash tools/build-rt-ac86u
```

The script builds the current committed revision fetched from this GitHub fork. Push changes before building; local uncommitted edits are not included. To rebuild another published revision:

```sh
bash tools/build-rt-ac86u 386.14_2
```

The toolchain image is pinned by digest and uses upstream's `bcm-hnd.sh` environment and `make rt-ac86u` target. Source checkout and compilation happen inside a case-sensitive Docker volume. Apple Silicon uses Linux amd64 emulation. Allow substantial disk space and several hours for a first build.

Images, SHA-256 checksums, and the source revision are written to `artifacts/<commit>/`. Build volumes are retained to avoid repeating source downloads; rebuilds clean generated files before compilation. Remove a volume when finished using `docker volume rm asuswrt-ac86u-<commit>`.

This is a repeatable source/toolchain setup, not a guarantee of byte-identical firmware: upstream embeds build metadata and timestamps. A successful compile does not verify operation on hardware. The RT-AC86U firmware format is `.w`; use only an image for this exact model.

## Check

```sh
python3 tools/test-build-rt-ac86u.py
```

Build procedure: [upstream documentation](https://github.com/RMerl/asuswrt-merlin.ng/wiki/Compile-Firmware-from-source).
