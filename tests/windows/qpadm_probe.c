/* T01 shared hash and Windows temporary-file ownership regression probe. */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <nicklib.h>
#include <xsearch.h>
#ifdef PROBE_BLOCKS
#include <mcio.h>
#include <qpsubs.h>
#endif

int main(int argc, char **argv)
{
    int mode, length, i;
    char key[512];
#ifdef PROBE_BLOCKS
    if (argc == 2 && !strcmp(argv[1], "blocks")) {
        int count = 1000001, blocks;
        SNP marker = {0};
        SNP **markers = calloc((size_t)count, sizeof(*markers));
        if (!markers) return 10;
        for (i = 0; i < count; ++i) markers[i] = &marker;
        setblocks(NULL, NULL, &blocks, markers, count, 0.0);
        free(markers);
        printf("blocks: %d\n", blocks);
        return blocks == count + 1 ? 0 : 11;
    }
#endif
    if (argc == 2 && !strcmp(argv[1], "hash")) {
        for (mode = 0; mode <= 2; ++mode) {
            setfancyhash(mode);
            for (length = 1; length < 512; ++length) {
                uint32_t value;
                unsigned char bytes[4];
                for (i = 0; i < length; ++i) key[i] = (char)(1 + (i*71 + length*31) % 255);
                key[length] = 0;
                value = (uint32_t)stringhash(key);
                for (i = 0; i < 4; ++i) bytes[i] = (unsigned char)(value >> (8*i));
                if (fwrite(bytes, 1, 4, stdout) != 4) return 1;
            }
        }
        return 0;
    }
#ifdef _WIN32
    if (argc == 2 && !strcmp(argv[1], "temp")) {
        char *candidate = mytemp("probe"), *reserved;
        char data[16] = {0};
        FILE *file = fopen(candidate, "wb");
        if (!file) return 2;
        fputs("preserve", file); fclose(file);
        reserved = admix_reserve_temp(candidate);
        if (!reserved || !strcmp(candidate, reserved)) return 3;
        file = fopen(candidate, "rb");
        if (!file) return 4;
        fread(data, 1, sizeof(data), file); fclose(file);
        if (strcmp(data, "preserve")) return 5;
        admix_release_temp(reserved, 0);
        if (!access(reserved, 0)) return 6;
        remove(candidate);
        free(reserved); free(candidate);
        candidate = mytemp("probe-exit");
        reserved = admix_reserve_temp(candidate);
        if (!reserved) return 7;
        free(reserved); free(candidate);
        puts("collision preserved; owned file removed; exit cleanup registered");
        return 0;
    }
    if (argc == 2 && !strcmp(argv[1], "fatal")) {
        char *candidate = mytemp("probe-fatal");
        char *reserved = admix_reserve_temp(candidate);
        if (!reserved) return 8;
        /* Leave both CRT stream and descriptor open at the fatal boundary. */
        if (!fopen(reserved, "rb") || open(reserved, O_RDONLY | O_BINARY) < 0) return 12;
        free(candidate); free(reserved);
        fatalx("intentional cleanup probe\n");
    }
    if (argc == 2 && !strcmp(argv[1], "write-failure")) {
        char *candidate = mytemp("probe-write");
        char *reserved = admix_reserve_temp(candidate);
        FILE *stream;
        if (!reserved) return 13;
        stream = fopen(reserved, "rb");
        if (!stream) return 14;
        /* Writing to a read-only stream sets ferror, independently of fclose. */
        if (fputs("cannot write", stream) >= 0 || !ferror(stream)) return 15;
        closeit_write(stream, reserved);
        return 16;
    }
#endif
    return 9;
}
