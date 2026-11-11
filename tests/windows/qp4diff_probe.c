/* Exercise the real T07 functions with bounded, directly constructed counts. */
#define main qp4diff_program_main
#include "../../src/qp4diff.c"
#undef main
#include <limits.h>

int main(int argc, char **argv)
{
  int data[4][4][2] = {{{3,9},{7,5},{4,8},{9,3}},
                       {{4,8},{8,4},{5,7},{8,4}},
                       {{5,7},{6,6},{3,9},{7,5}},
                       {{2,10},{8,4},{6,6},{10,2}}};
  int *pops[4][4], **counts[4], blocks[4]={0,0,1,2};
  int top[4]={0,1,2,3}, bottom[4]={0,2,1,3};
  double value, sd;
  if (argc!=2) return 2;
  for (int s=0;s<4;++s) {
    counts[s]=pops[s];
    for (int p=0;p<4;++p) pops[s][p]=data[s][p];
  }
  if (!strcmp(argv[1],"f4")) {
    int repeat[4]={0,1,0,1};
    int absent[4]={-1,1,2,3};
    int ret=getf4(counts[0],top,&value); printf("ordinary %d %.12f\n",ret,value);
    ret=getf4(counts[0],repeat,&value); printf("overlap %d %.12f\n",ret,value);
    ret=getf4(counts[0],absent,&value); printf("NULL %d %.12f\n",ret,value);
    for(int p=0;p<4;++p) data[0][p][0]=data[0][p][1]=INT_MAX;
    ret=getf4(counts[0],repeat,&value); printf("large %d %.12f\n",ret,value);
    return 0;
  }
  overlap = strstr(argv[1],"nonoverlap") ? NO : YES;
  if (!strncmp(argv[1],"lifetime",8)) {
    for(int i=0;i<16;++i) {
      int n=doq4diff(&value,&sd,counts,blocks,12,4,top,bottom,4,3);
      if(n!=4 || !isfinite(value) || !isfinite(sd)) return 3;
    }
    puts("16 finite workspace lifetimes"); return 0;
  }
  if (!strncmp(argv[1],"one-block",9)) {
    for(int s=0;s<4;++s) blocks[s]=0;
    int n=doq4diff(&value,&sd,counts,blocks,12,4,top,bottom,4,3);
    printf("single-block return %d\n",n); return n==-999 ? 0 : 3;
  }
  if (!strncmp(argv[1],"upper-block",11)) blocks[0]=3;
  if (!strncmp(argv[1],"negative-block",14)) for(int s=0;s<4;++s) blocks[s]=-1;
  if (!strcmp(argv[1],"NULL-left")) top[0]=-1;
  if (!strcmp(argv[1],"NULL-right")) bottom[0]=-1;
  int n=doq4diff(&value,&sd,counts,blocks,!strcmp(argv[1],"zero-rows")?0:12,4,top,bottom,4,3);
  printf("return %d\n",n); return 0;
}
