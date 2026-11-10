/* Exercise the real index guard without allocating multi-gigabyte matrices.
 * Link with function/data sections and --gc-sections plus libnick. */
#define main qpfstats_program_main
#include "../../src/qpfstats.c"
#undef main

int main(int argc, char **argv)
{
  char *names[2] = {NULL, NULL};
  int n;
  if (argc == 6 && strcmp(argv[1], "sample") == 0) {
    Indiv **people;
    int count, rows, i, limit = atoi(argv[4]);
    char **pops;
    count = getindivs(argv[2], &people);
    rows = numlines(argv[3]);
    ZALLOC(pops, rows, char *);
    rows = loadlist_capacity(pops, argv[3], rows);
    setgk(people, count, argv[3], NULL, NULL);
    gkignore(people, count);
    SRAND((unsigned int)strtoul(argv[5], NULL, 10));
    setplimit(people, count, pops, rows, limit);
    for (i = 0; i < count; ++i) if (!people[i]->ignore) printf("%d\n", i);
    return 0;
  }
  if (argc == 2 && strcmp(argv[1], "duplicate") == 0) {
    char *keys[] = {"z", "z", "a"};
    n = finddupalt(keys, 3);
    printf("duplicate: %s\n", n < 0 ? "none" : keys[n]);
    return n >= 0 && !strcmp(keys[n], "z") ? 0 : 1;
  }
  if (argc == 2 && (!strcmp(argv[1], "temp") || !strcmp(argv[1], "fatal") || !strcmp(argv[1], "keep"))) {
    char *candidate = mytemp("owned"), *path, *collision;
    FILE *file;
    openit(candidate, &file, "w");
    fputs("sentinel", file);
    closeit_write(file, candidate);
    path = reserve_temp("owned");
    if (path == NULL || !strcmp(path, candidate)) return 10;
    collision = path;
    openit(path, &file, "r");
    printf("reserved: %s\n", path);
    if (!strcmp(argv[1], "fatal")) fatalx("owned temporary cleanup probe\n");
    fclose(file);
    if (!strcmp(argv[1], "keep")) release_temp(path, 1);
    free(collision);
    free(candidate);
    return 0;
  }
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
