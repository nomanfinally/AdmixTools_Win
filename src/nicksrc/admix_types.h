#ifndef ADMIXTOOLS_TYPES_H
#define ADMIXTOOLS_TYPES_H
#include <stdint.h>
#include <inttypes.h>
#include <limits.h>

/* Preserve upstream LP64 integer arithmetic on Windows' LLP64 data model.
 * LAPACK integers remain 32-bit and are deliberately not expressed here.
 */
#ifdef _WIN32
typedef int64_t admix_long;
typedef uint64_t admix_ulong;
#define ADMIX_LONG_MAX INT64_MAX
#define ADMIX_PRIdLONG PRId64
#define ADMIX_PRIiLONG PRIi64
#define ADMIX_PRIuLONG PRIu64
#define ADMIX_PRIoLONG PRIo64
#define ADMIX_PRIxLONG PRIx64
#define ADMIX_PRIXLONG PRIX64
#else
typedef long admix_long;
typedef unsigned long admix_ulong;
#define ADMIX_LONG_MAX LONG_MAX
#define ADMIX_PRIdLONG "ld"
#define ADMIX_PRIiLONG "li"
#define ADMIX_PRIuLONG "lu"
#define ADMIX_PRIoLONG "lo"
#define ADMIX_PRIxLONG "lx"
#define ADMIX_PRIXLONG "lX"
#endif
#endif
