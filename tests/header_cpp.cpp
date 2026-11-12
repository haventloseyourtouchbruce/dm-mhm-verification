#include "dm_mhm_abi.h"
#include <type_traits>
static_assert(std::is_same_v<decltype(dm_mhm_abi_version()), uint32_t>);
static_assert(sizeof(int64_t) == 8);
int dm_mhm_header_cpp_check() { return static_cast<int>(DM_MHM_ABI_VERSION); }
