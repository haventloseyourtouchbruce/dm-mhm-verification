#ifndef DM_MHM_ABI_H
#define DM_MHM_ABI_H
#include <stddef.h>
#include <stdint.h>
#if defined(_WIN32) || defined(__CYGWIN__)
# ifdef DM_MHM_BUILD_DLL
#  define DM_MHM_API __declspec(dllexport)
# else
#  define DM_MHM_API __declspec(dllimport)
# endif
#elif defined(__GNUC__) || defined(__clang__)
# define DM_MHM_API __attribute__((visibility("default")))
#else
# define DM_MHM_API
#endif
#ifdef __cplusplus
extern "C" {
#endif
typedef struct dm_mhm_ctx dm_mhm_ctx_t;
enum {
    DM_MHM_OK = 0, DM_MHM_INVALID = 1, DM_MHM_CAPACITY = 2,
    DM_MHM_UNLOADED = 3, DM_MHM_UNSUPPORTED = 4,
    DM_MHM_NO_MEMORY = 5, DM_MHM_DEBUGGER_DETECTED = 6
};
#define DM_MHM_ABI_VERSION 1u
#define DM_MHM_PEAK_CAPACITY 4096u
#define DM_MHM_MAX_HARMONICS 32u
#define DM_MHM_Q32_ONE INT64_C(4294967296)
#define DM_MHM_MAX_FREQUENCY_Q32 INT64_C(8589934592000)
DM_MHM_API uint32_t dm_mhm_abi_version(void);
DM_MHM_API int32_t dm_mhm_create(dm_mhm_ctx_t **out_ctx);
DM_MHM_API int32_t dm_mhm_load_peaks(dm_mhm_ctx_t *ctx,
    const int64_t *peaks_q32, size_t peak_count);
DM_MHM_API int32_t dm_mhm_match_batch(dm_mhm_ctx_t *ctx,
    const int64_t *queries_q32, size_t query_count, uint32_t harmonic_count,
    int64_t tolerance_q32, int64_t *out_matches_q32, uint8_t *out_restart_flags);
DM_MHM_API void dm_mhm_destroy(dm_mhm_ctx_t *ctx);
#ifdef __cplusplus
}
#endif
#endif
