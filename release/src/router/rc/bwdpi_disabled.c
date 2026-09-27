#include <stdint.h>
#include <stddef.h>

struct udb_ioc_entry;

int check_tdts_module_exist(void) { return 0; }
int check_bwdpi_nvram_setting(void) { return 0; }
int check_wrs_switch(void) { return 0; }

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
