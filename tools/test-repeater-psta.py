from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]
services = (root / "release/src/router/rc/services.c").read_text()
source = services.split("static void configure_repeater_psta(void)", 1)[1].split("\n#endif", 1)[0]
harness = r'''
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
static char *setting = "1", *mode = "wet", *auth = "psk2", *crypto = "aes";
static char *interface = "eth6", *ssid = "test network";
static int repeater = 1, psta = 0, wet = 1, query_failure, command_failure;
static int queries, commands, messages;
static char recorded[16][256];
static int nvram_match(const char *name, const char *value) {
    const char *actual = !strcmp(name, "bl4ko_psta") ? setting :
        !strcmp(name, "wl1_mode") ? mode :
        !strcmp(name, "wlc_auth_mode") ? auth : crypto;
    return !strcmp(actual, value);
}
static char *nvram_safe_get(const char *name) {
    return !strcmp(name, "wl1_ifname") ? interface : ssid;
}
static int is_psr(int unit) { assert(unit == 1); return repeater; }
static int wl_iovar_getint(char *ifname, char *name, int *value) {
    assert(!strcmp(ifname, "eth6"));
    queries++;
    if (queries == query_failure) return -1;
    *value = !strcmp(name, "psta") ? psta : wet;
    return 0;
}
static int record(const char *first, ...) {
    va_list arguments;
    const char *value;
    size_t length;
    assert(commands < 16);
    snprintf(recorded[commands], sizeof(recorded[commands]), "%s", first);
    va_start(arguments, first);
    while ((value = va_arg(arguments, const char *))) {
        length = strlen(recorded[commands]);
        snprintf(recorded[commands] + length, sizeof(recorded[commands]) - length, "|%s", value);
    }
    va_end(arguments);
    return ++commands == command_failure;
}
#define eval(...) record(__VA_ARGS__, (char *)NULL)
static void logmessage(const char *name, const char *message) {
    assert(!strcmp(name, "repeater") && *message);
    messages++;
}
'''
checks = r'''
static void reset(void) {
    queries = commands = messages = command_failure = query_failure = 0;
    memset(recorded, 0, sizeof(recorded));
}
static void skipped(void) {
    reset();
    configure_repeater_psta();
    assert(!commands && !messages);
}
int main(void) {
    setting = ""; skipped(); setting = "0"; skipped(); setting = "2"; skipped(); setting = "1";
    repeater = 0; skipped(); repeater = 1;
    mode = "ap"; skipped(); mode = "wet";
    auth = "sae"; skipped(); auth = "psk2";
    crypto = "tkip"; skipped(); crypto = "aes";
    interface = ""; skipped(); interface = "eth6";
    ssid = ""; skipped(); ssid = "test network";
    psta = 1; wet = 0; skipped();
    psta = 2; skipped(); psta = 0; skipped(); wet = 1;
    for (int step = 1; step <= 2; step++) {
        reset(); query_failure = step;
        configure_repeater_psta();
        assert(queries == step && !commands && !messages);
    }
    reset();
    configure_repeater_psta();
    assert(commands == 5 && messages == 1);
    const char *expected[] = {
        "wl|-i|eth6|down", "wl|-i|eth6|wet_enab|0", "wl|-i|eth6|psta|1",
        "wl|-i|eth6|up", "wl|-i|eth6|join|test network|imode|bss|amode|wpa2psk"
    };
    for (int step = 0; step < 5; step++) assert(!strcmp(recorded[step], expected[step]));
    const char *restore[] = {
        "wl|-i|eth6|down", "wl|-i|eth6|psta|0", "wl|-i|eth6|wet_enab|1",
        "wl|-i|eth6|up", "wl|-i|eth6|join|test network|imode|bss|amode|wpa2psk"
    };
    for (int failure = 1; failure <= 5; failure++) {
        reset(); command_failure = failure;
        configure_repeater_psta();
        assert(commands == failure + 5 && messages == 1);
        for (int step = 0; step < 5; step++) assert(!strcmp(recorded[failure + step], restore[step]));
    }
}
'''
with tempfile.TemporaryDirectory() as directory:
    c_file = Path(directory) / "psta.c"
    binary = Path(directory) / "psta"
    c_file.write_text(harness + "\nstatic void configure_repeater_psta(void)" + source + checks)
    subprocess.run(["cc", "-std=c99", "-Wall", "-Wextra", "-Werror", str(c_file), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

start = services.split("\nstart_psta_monitor()", 1)[1].split("\n}\n", 1)[0]
assert start.index("configure_repeater_psta();") < start.index("return _eval(psta_monitor_argv")
print("Repeater PSTA control and rollback checks passed")
