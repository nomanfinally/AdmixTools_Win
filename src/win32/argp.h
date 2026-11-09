#ifndef ADMIXTOOLS_WIN32_ARGP_H
#define ADMIXTOOLS_WIN32_ARGP_H
#include <argp.h>
#include <string.h>
#include <stdlib.h>

/* GNU argp recognizes '/' as a path separator. Supply the equivalent native
 * basename and omit the executable extension so help wraps just as on Linux.
 */
static inline error_t admix_argp_parse(const struct argp *parser, int argc,
    char **argv, unsigned flags, int *index, void *input)
{
    char *original = argv[0], *name, *slash, *backslash;
    error_t result;
    size_t length;
    if (!original) return argp_parse(parser, argc, argv, flags, index, input);
    slash = strrchr(original, '/');
    backslash = strrchr(original, '\\');
    name = original;
    if (slash) name = slash + 1;
    if (backslash && backslash + 1 > name) name = backslash + 1;
    name = strdup(name);
    if (!name) return ENOMEM;
    length = strlen(name);
    if (length >= 4 && strcasecmp(name + length - 4, ".exe") == 0)
        name[length - 4] = '\0';
    argv[0] = name;
    result = argp_parse(parser, argc, argv, flags, index, input);
    argv[0] = original;
    free(name);
    return result;
}
#define argp_parse admix_argp_parse
#endif
