/* Exercise the real index guard without allocating multi-gigabyte matrices.
 * Link with function/data sections and --gc-sections plus libnick. */
#define main qpfstats_program_main
#include "../../src/qpfstats.c"
#undef main

int main(int argc, char **argv)
{
  char *names[2] = {NULL, NULL};
  int n;
  if (argc == 3 && strcmp(argv[1], "dimensions") == 0) {
    checkdimensions(atoi(argv[2]));
    puts("dimensions accepted");
    return 0;
  }
  if (argc == 4 && strcmp(argv[1], "list") == 0) {
    n = loadlist_capacity(names, argv[3], atoi(argv[2]));
    printf("list: %d %s %s\n", n, n > 0 ? names[0] : "NULL",
           n > 1 ? names[1] : "NULL");
    return 0;
  }
  return 2;
}
