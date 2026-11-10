/* Native child for the M01 CRT argument-quotation oracle. */
#include <stdio.h>
#include <string.h>
int main(int argc,char **argv) {
  int i;
  for(i=1;i<argc;++i) {
    unsigned char *p=(unsigned char *)argv[i];
    printf("arg %d:",i);
    while(*p) printf("%02x",*p++);
    putchar('\n');
  }
  return argc>1 && !strcmp(argv[1],"--exit=7") ? 7:0;
}
