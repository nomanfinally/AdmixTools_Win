#ifndef ADMIXTOOLS_WIN32_MMAN_H
#define ADMIXTOOLS_WIN32_MMAN_H

#include <stddef.h>
#include <stdint.h>
#include <errno.h>
#include <io.h>
#include <windows.h>

#define PROT_READ 1
#define MAP_PRIVATE 2
#define MAP_POPULATE 0
#define MAP_FAILED ((void *)-1)

/* Upstream only maps entire files read-only, privately, from offset zero. */
static inline void *mmap(void *address, size_t length, int protection,
                         int flags, int fd, int64_t offset)
{
    HANDLE file, mapping;
    void *view;
    if (address || !length || protection != PROT_READ ||
        flags != MAP_PRIVATE || offset != 0) {
        errno = EINVAL;
        return MAP_FAILED;
    }
    file = (HANDLE)_get_osfhandle(fd);
    if (file == INVALID_HANDLE_VALUE) { errno = EBADF; return MAP_FAILED; }
    mapping = CreateFileMappingA(file, NULL, PAGE_READONLY, 0, 0, NULL);
    if (!mapping) { errno = EIO; return MAP_FAILED; }
    view = MapViewOfFile(mapping, FILE_MAP_READ, 0, 0, length);
    CloseHandle(mapping);
    if (!view) { errno = ENOMEM; return MAP_FAILED; }
    return view;
}

static inline int munmap(void *address, size_t length)
{
    (void)length;
    if (UnmapViewOfFile(address)) return 0;
    errno = EINVAL;
    return -1;
}
#endif
