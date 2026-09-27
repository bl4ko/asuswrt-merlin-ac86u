#include <stdint.h>
#include <stddef.h>

struct udb_ioc_entry;

#ifndef RTCONFIG_BWDPI
int check_tdts_module_exist(void) { return 0; }
int check_bwdpi_nvram_setting(void) { return 0; }
int check_wrs_switch(void) { return 0; }
int check_tcode_blacklist(void) { return 1; }
int dump_dpi_support(int index) { return 0; }

int get_fw_mesh_extender(void **output, unsigned int *used_len)
{
	if (output) *output = NULL;
	if (used_len) *used_len = 0;
	return -1;
}

int get_fw_user_list(struct udb_ioc_entry **output, uint32_t *used_len)
{
	if (output) *output = NULL;
	if (used_len) *used_len = 0;
	return -1;
}

int mesh_set_extender(char *macstr, uint8_t action) { return -1; }
#endif

#ifndef RTCONFIG_TUNNEL
int aae_sendIpcMsgAndWaitResp(char *path, char *data, int data_len, char *out, int out_len, int timeout)
{
	if (out && out_len > 0) out[0] = '\0';
	return -1;
}
#endif
