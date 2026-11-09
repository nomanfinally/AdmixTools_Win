#ifndef ADMIXTOOLS_WIN32_COMPAT_H
#define ADMIXTOOLS_WIN32_COMPAT_H

#ifdef _WIN32
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <direct.h>

/* Keep the Linux random() stream; the CRT rand() is a different generator. */
long admix_random(void);
void admix_srandom(unsigned int seed);
#define random admix_random
#define srandom admix_srandom
int admix_setenv(const char *name, const char *value, int overwrite);
#define setenv admix_setenv

ssize_t admix_getline(char **line, size_t *capacity, FILE *stream);
#define getline admix_getline
#define mkdir(path, mode) _mkdir(path)

/* MinGW's default stat and lseek can truncate files above 2 GiB. */
#define stat _stat64
#define fstat _fstat64
#define lseek _lseeki64

const char *admix_tempdir(void);
int admix_filter_fstats(const char *input, const char *output);
int admix_copy_file(const char *input, const char *output);
int admix_gunzip(const char *input, const char *output);
int admix_run_qpfstats(const char *parameters, const char *logfile);
int admix_run_sibling(const char *name, const char *const arguments[], const char *logfile);
int admix_render_graph(const char *dotfile, const char *psfile);
double admix_cpu_seconds(void);
double admix_memory_bytes(void);
#endif
#endif
