from pathlib import Path
import os
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
router = root / "release/src/router"
target = (root / "release/src-rt/target.mak").read_text().split("export RT-AC86U +=", 1)[1].split("export GT-AC2900", 1)[0]
for flag in ("WEBDAV", "SMARTSYNCBASE", "NATNL_AICLOUD", "NATNL_AIHOME", "BWDPI", "WTFAST", "PARENTAL2", "GETREALIP", "UUPLUGIN", "ASD", "LETSENCRYPT", "INSTANT_GUARD", "OOKLA"):
    assert f"{flag}=n" in target
assert "ASUSCTRL=y" in target
assert "CONFIG_IP6_NF_RAW=y" in (root / "release/src-rt-5.02hnd/kernel/linux-4.1/config_base.6a").read_text()
assert "menu_AiCloud" not in (router / "www/require/menuTrees/menuTree_no_bwdpi.js").read_text()

for name in ("rc/usb.c", "rc/services.c", "rc/firewall.c", "httpd/web.c", "httpd/httpd.c"):
    source = (router / name).read_text()
    source = re.sub(r'^\s*#\s*include[^\n]*', '', source, flags=re.M)
    output = subprocess.check_output(["cc", "-E", "-P", "-x", "c", "-DRTCONFIG_USB", "-DKERNEL_VERSION(a,b,c)=((a<<16)+(b<<8)+c)", "-"], input=source, text=True)
    assert "S50aicloud" not in output and "S50smartsync" not in output, name
    if name == "rc/usb.c":
        assert "lighttpd" not in output
        for signature in ("start_webdav(void)", "stop_webdav(void)", "start_cloudsync(int fromUI)", "stop_cloudsync(int type)"):
            assert re.search(re.escape(signature) + r"\s*\{\s*\}", output), signature
    if name == "rc/firewall.c":
        assert 'nvram_get_int("webdav_aidisk")' not in output
    if name == "httpd/httpd.c":
        assert "cloud_sync.asp" not in output
    if name == "httpd/web.c":
        assert '"get_sharelink"' not in output
        assert '"UI_cloud_status"' not in output

with tempfile.TemporaryDirectory() as directory:
    nvram = Path(directory) / "nvram"
    nvram.write_text("#!/bin/sh\nexit 0\n")
    nvram.chmod(0o755)
    for package in ("aicloud", "smartsync"):
        result = subprocess.run(["sh", str(router / "rom/apps_scripts/app_install.sh"), package], env=dict(os.environ, PATH=f"{directory}:{os.environ['PATH']}"), capture_output=True)
        assert result.returncode == 1 and not result.stderr, result

    guard = (router / "rom/apps_scripts/app_init_run.sh").read_text().split('tmp_apps_name=`get_apps_name $f`', 1)[1].split('if [ "$1" != "allpkg" ]', 1)[0]
    for package, action, expected in (("aicloud", "start", ""), ("smartsync", "start", ""), ("aicloud", "stop", "run\n"), ("downloadmaster", "start", "run\n")):
        shell = f'tmp_apps_name={package}\nset -- allpkg {action}\nfor item in once; do\n{guard}\necho run\ndone'
        output = subprocess.check_output(["sh", "-c", shell], env=dict(os.environ, PATH=f"{directory}:{os.environ['PATH']}"), text=True)
        assert output == expected, (package, action, output)


print("Cloud removal checks passed")

with tempfile.TemporaryDirectory() as directory:
    source = (router / "shared/disabled_services.c").read_text() + r'''
#include <assert.h>
int main(void) {
    void *mesh = (void *)1;
    struct udb_ioc_entry *users = (void *)1;
    unsigned int mesh_len = 1;
    uint32_t user_len = 1;
    assert(!check_tdts_module_exist() && !check_bwdpi_nvram_setting() && !check_wrs_switch());
    assert(get_fw_mesh_extender(&mesh, &mesh_len) == -1 && !mesh && !mesh_len);
    assert(get_fw_user_list(&users, &user_len) == -1 && !users && !user_len);
    assert(get_fw_mesh_extender(NULL, NULL) == -1 && get_fw_user_list(NULL, NULL) == -1);
    assert(mesh_set_extender(NULL, 0) == -1);
    assert(check_tcode_blacklist() == 1 && dump_dpi_support(0) == 0);
    char out[] = "unchanged";
    assert(aae_sendIpcMsgAndWaitResp(NULL, NULL, 0, out, sizeof(out), 0) == -1 && !out[0]);
    assert(aae_sendIpcMsgAndWaitResp(NULL, NULL, 0, NULL, 0, 0) == -1);
}
'''
    binary = str(Path(directory) / "check")
    subprocess.run(["cc", "-x", "c", "-o", binary, "-"], input=source, text=True, check=True)
    subprocess.run([binary], check=True)

source = (router / "rc/lan.c").read_text()
helper = source.split("int restrict_router_egress(void)", 1)[1].split("\n#endif", 1)[0]
harness = r'''
#include <arpa/inet.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static char *address, *mask;
static char *nvram_safe_get(const char *name) {
    return !strcmp(name, "lan_ipaddr") ? address : mask;
}
static void ip2class(char *address, char *mask, char *output) {
    snprintf(output, 32, "%s/%s", address, mask);
}
static void logmessage(const char *name, const char *message) {}
static int record(const char *first, ...) {
    va_list arguments;
    const char *value;
    int check = 0, policy = 0;
    printf("%s", first);
    va_start(arguments, first);
    while ((value = va_arg(arguments, const char *))) {
        printf(" %s", value);
        if (!strcmp(value, "-C")) check = 1;
        if (!strcmp(value, "-P")) policy = 1;
    }
    va_end(arguments);
    puts("");
    return check || (policy && getenv("FAIL_POLICY"));
}
#define eval(...) record(__VA_ARGS__, (char *)NULL)
'''
with tempfile.TemporaryDirectory() as directory:
    c_file = Path(directory) / "egress.c"
    program = Path(directory) / "egress"
    c_file.write_text(harness + "\nstatic int restrict_router_egress(void)" + helper + '\nint main(int argc, char **argv) { address=argv[1]; mask=argv[2]; return restrict_router_egress(); }\n')
    subprocess.run(["cc", "-Wall", "-Werror", str(c_file), "-o", str(program)], check=True)
    commands = subprocess.check_output([str(program), "10.0.2.113", "255.255.255.0"], text=True)
    assert "iptables -t raw -P OUTPUT DROP" in commands
    assert "ip6tables -t raw -P OUTPUT DROP" in commands
    assert "-d 10.0.1.0/24 -j ACCEPT" in commands
    assert "-d 10.0.2.113/255.255.255.0 -j ACCEPT" in commands
    assert "-d fe80::/10 -j ACCEPT" in commands and "-d ff02::/16 -j ACCEPT" in commands
    assert "FORWARD" not in commands and "PREROUTING" not in commands
    for address, mask in (("10.0.2.113", "0.0.0.0"), ("10.0.2.113", "255.0.255.0"), ("bad", "255.255.255.0")):
        output = subprocess.check_output([str(program), address, mask], text=True)
        assert f"-d {address}/{mask}" not in output
    failed = subprocess.run([str(program), "10.0.2.113", "255.255.255.0"], env=dict(os.environ, FAIL_POLICY="1"), capture_output=True, text=True)
    assert failed.returncode != 0 and "-A" not in failed.stdout
print("Router egress checks passed")
