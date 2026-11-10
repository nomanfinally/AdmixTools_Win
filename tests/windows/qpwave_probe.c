/* Exercise the actual guard without allocating multi-gigabyte matrices. */
#define main qpwave_program_main
#include "../../src/qpWave.c"
#undef main

int main(int argc, char **argv)
{
  if (argc != 3) return 2;
  checkdimensions(atoi(argv[1]), atoi(argv[2]));
  puts("qpWave dimensions accepted");
  return 0;
}
