/* T03: exercise constructMap's real failure path without exhausting memory.
 * Linux only: cap this process's address space, then map a sparse 4-GiB file.
 * Compile with function sections and --gc-sections plus the real libnick.
 * Exit 10 means MAP_FAILED escaped as a live genFile (the audited defect).
 */
#ifdef QPWAVE_FORCE_MAP_FAILURE
/* Include the platform declaration first; replace only this probe's call site.
 * The production constructMap implementation and failure cleanup execute. */
#include <errno.h>
#ifdef _WIN32
#include "../../src/win32/mman.h"
#else
#include <sys/mman.h>
#endif
#define mmap(address, length, protection, flags, fd, offset) (errno = ENOMEM, MAP_FAILED)
#endif
#include "../../src/mapfile.c"
#if defined(_WIN32) && defined(QPWAVE_FORCE_MAP_FAILURE)
/* PE linking retains the legacy caller references; supply its real globals
 * and link the ordinary qpWave dependency objects (excluding mapfile.o). */
#define main qpwave_program_main
#include "../../src/qpWave.c"
#undef main
#endif
#ifdef QPWAVE_FORCE_MAP_FAILURE
int main(int argc, char **argv)
{
  int fd;
  if (argc != 2) return 2;
  fd = open(argv[1], O_WRONLY | O_CREAT | O_EXCL, 0600);
  if (fd < 0) return 3;
  if (write(fd, "x", 1) != 1) { close(fd); return 4; }
  close(fd);
  constructMap(argv[1], 1, 1, 0);
  return 10; /* A failed mapping must never return to the caller. */
}
#elif !defined(_WIN32)
#include <sys/resource.h>

int main(int argc, char **argv)
{
  const off_t length = (off_t)4294967300LL;
  unsigned long pages;
  FILE *status;
  int fd;
  struct rlimit limit;
  genFile *mapping;
  if (argc != 2) return 2;
  status = fopen("/proc/self/statm", "r");
  if (!status || fscanf(status, "%lu", &pages) != 1) return 3;
  fclose(status);
  if (getrlimit(RLIMIT_AS, &limit)) return 4;
  limit.rlim_cur = (rlim_t)pages * sysconf(_SC_PAGESIZE) + 64 * 1024 * 1024;
  if (limit.rlim_max != RLIM_INFINITY && limit.rlim_cur > limit.rlim_max) return 5;
  fd = open(argv[1], O_RDWR | O_CREAT | O_EXCL, 0600);
  if (fd < 0) return 6;
  if (ftruncate(fd, length)) { close(fd); remove(argv[1]); return 7; }
  close(fd);
  if (setrlimit(RLIMIT_AS, &limit)) { remove(argv[1]); return 8; }
  mapping = constructMap(argv[1], 4, length / 4, 0);
  if (mapping->snps == MAP_FAILED) {
    puts("BUG: constructMap returned MAP_FAILED as a live genotype mapping");
    free(mapping);
    remove(argv[1]);
    return 10;
  }
  destroyMap(mapping);
  remove(argv[1]);
  return 9; /* The failure injection did not take effect. */
}
#else
int main(void) { return 77; } /* No RLIMIT_AS equivalent used on Windows. */
#endif
