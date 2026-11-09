/* Compare this output against glibc and the original Linux libnick.a. */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <admix_types.h>
#include <nicklib.h>

int main(int argc, char **argv)
{
    unsigned int seeds[] = {0, 1, 2, 77, 123456789, 2147483647U, 2147483648U, 4294967295U};
    size_t i;
    int j;
    if (argc == 2) {
        /* Serialize explicitly so host endianness and sizeof(long) cannot hide
         * sequence differences. 800,000 outputs include wraparound/reseeding. */
        for (i = 0; i < sizeof(seeds)/sizeof(seeds[0]); ++i) {
            srandom(seeds[i]);
            for (j = 0; j < 100000; ++j) {
                uint32_t value = (uint32_t)random();
                unsigned char bytes[4] = {value & 255, (value >> 8) & 255,
                    (value >> 16) & 255, (value >> 24) & 255};
                if (fwrite(bytes, 1, 4, stdout) != 4) return 1;
            }
        }
    } else {
        double values[] = {3000000000.0, -3000000000.0, 1000000000000.0, 2.5, 3.5, -2.5};
        admix_long rounded[6];
        int keys[64], order[64];
        fixitl(rounded, values, 6);
        for (j = 0; j < 6; ++j) printf("%" ADMIX_PRIdLONG "\n", rounded[j]);
        for (j = 0; j < 64; ++j) keys[j] = j % 4;
        isortit(keys, order, 64);
        for (j = 0; j < 64; ++j) printf("%d %d\n", keys[j], order[j]);
    }
    return 0;
}
