#include "dm_mhm_abi.h"
_Static_assert(sizeof(int64_t) == 8, "64-bit words required");
_Static_assert(DM_MHM_ABI_VERSION == 1u, "ABI version");
int dm_mhm_header_c_check(void) { return (int)DM_MHM_ABI_VERSION; }
