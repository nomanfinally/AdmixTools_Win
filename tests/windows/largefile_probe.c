#include <stdio.h>
#include <stdint.h>
#include <fcntl.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#ifdef _WIN32
#include "win32/mman.h"
#include <winioctl.h>
#else
#include <sys/mman.h>
#endif

int main(int argc, char **argv)
{
    const int64_t length = INT64_C(4294967300);
    const unsigned char expected[4] = {0x0a, 0x0d, 0x1a, 0xff};
    struct stat info;
    int fd;
    unsigned char *data;
    if (argc != 2) return 1;
    fd = open(argv[1], O_CREAT | O_TRUNC | O_RDWR, 0600);
    if (fd < 0) return 2;
#ifdef _WIN32
    {
        DWORD returned;
        if (!DeviceIoControl((HANDLE)_get_osfhandle(fd), FSCTL_SET_SPARSE,
            NULL, 0, NULL, 0, &returned, NULL)) return 3;
        if (_chsize_s(fd, length)) return 4;
    }
#else
    if (ftruncate(fd, length)) return 4;
#endif
    if (lseek(fd, length - 4, SEEK_SET) != length - 4) return 5;
    if (write(fd, expected, 4) != 4) return 6;
    if (fstat(fd, &info) || info.st_size != length) return 7;
    data = mmap(NULL, (size_t)length, PROT_READ, MAP_PRIVATE, fd, 0);
    close(fd);
    if (data == MAP_FAILED) return 8;
    if (memcmp(data + length - 4, expected, 4)) return 9;
    if (munmap(data, (size_t)length)) return 10;
    if (remove(argv[1])) return 11;
    puts("64-bit size, seek, binary I/O and mapping beyond 4 GiB: OK");
    return 0;
}
