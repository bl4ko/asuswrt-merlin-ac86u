# RT-AC86U build

Personal fork of [Asuswrt-Merlin](https://github.com/RMerl/asuswrt-merlin.ng), based on tag `386.14_2`, commit `6a5df61aab6f3fa2dffc518994d42e4f2a27fb2b`.

The `rt-ac86u` branch replaces the Merlin banner with **Powered by bl4ko**, applies a Tokyo Night theme, and removes AiCloud, Smart Sync, WebDAV and the shared ASUS remote-access tunnel. It also disables ASUS cloud security and gaming add-ons, public-IP detection, online speed tests, Let’s Encrypt and Instant Guard. Upstream source attribution and licenses are retained.

The router itself is restricted to its configured IPv4 LAN subnet, Smartno's `10.0.1.0/24` management subnet, loopback, local multicast and DHCP broadcasts. IPv6 traffic from the router is limited to loopback, link-local addresses and link-local multicast. These outbound rules load before LAN startup, refresh on DHCP changes and survive normal firewall reloads. They leave bridged Wi-Fi clients’ internet traffic available. Use a DNS or time server in one of the allowed LAN subnets; internet firmware checks and package downloads cannot work.

This does not enable UniFi adoption or add security fixes beyond upstream 386.14_2. The firmware is being validated locally and has not been tested on hardware.

## Build

Install and start Docker, then run from this repository:

```sh
bash tools/build-rt-ac86u
```

The script builds the current local committed revision through a read-only repository mount. No GitHub push is required; uncommitted edits are not included. To rebuild another local revision:

```sh
bash tools/build-rt-ac86u 386.14_2
```

The toolchain image is pinned by digest and uses upstream's `bcm-hnd.sh` environment and `make rt-ac86u` target as its unprivileged `docker` user. Package compilation uses 12 workers while preserving the order between packages; override with `BUILD_JOBS=4 bash tools/build-rt-ac86u`. Source checkout and compilation happen inside a case-sensitive Docker volume. Apple Silicon uses Linux amd64 emulation, and the legacy ARM compiler is a 32-bit x86 executable. Configuration probes remain serial. Allow substantial disk space and several hours for a first build. A partial clone needs the selected model's source objects cached locally before building.

Images, SHA-256 checksums, and the source revision are written to `artifacts/<commit>/`. Build volumes are retained to avoid repeating source downloads; rebuilds clean generated files before compilation. Remove a volume when finished using `docker volume rm asuswrt-ac86u-<commit>`.

This is a repeatable source/toolchain setup, not a guarantee of byte-identical firmware: upstream embeds build metadata and timestamps. A successful compile does not verify operation on hardware. The RT-AC86U firmware format is `.w`; use only an image for this exact model.

## Check

```sh
python3 tools/test-build-rt-ac86u.py
python3 tools/test-ac86u-custom.py
```

Build procedure: [upstream documentation](https://github.com/RMerl/asuswrt-merlin.ng/wiki/Compile-Firmware-from-source).
