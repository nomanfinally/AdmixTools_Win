/* Production T06 routines with their ordinary globals/link inputs. */
#define main qpf4ratio_program_main
#include "../../src/qpF4ratio.c"
#undef main
#include <limits.h>
extern int packmode;

int main(int argc, char **argv)
{
  if (argc != 2) return 2;
  if (!strncmp(argv[1], "sampling-", 9)) {
    unsigned int sample_seed; int limit;
    char *all[]={"Out","A","B","C","X","R1","R2","R3","R4"};
    char *pops[]={"Out","A","B","C","X"};
    if (sscanf(argv[1],"sampling-%u-%d",&sample_seed,&limit)!=2 || limit<1) return 2;
    numindivs=54;ZALLOC(indivmarkers,numindivs,Indiv *);
    for(int i=0;i<numindivs;++i) {
      ZALLOC(indivmarkers[i],1,Indiv);indivmarkers[i]->egroup=strdup(all[i/6]);
      indivmarkers[i]->ignore=(i>=30);
    }
    SRAND(sample_seed);setplimit(indivmarkers,numindivs,pops,5,limit);
    for(int i=0;i<numindivs;++i) {
      if(!indivmarkers[i]->ignore) printf("%d\n",i);
      free(indivmarkers[i]->egroup);free(indivmarkers[i]);
    }
    free(indivmarkers);return 0;
  }
  if (!strncmp(argv[1],"banker-",7)) {
    int types[101]={0},quad[4]={97,98,99,100};
    types[97]=1;types[98]=types[99]=2;
    if(!strcmp(argv[1],"banker-index"))quad[0]=101;
    if(!strcmp(argv[1],"banker-type"))types[97]=3;
    if(!islegal(quad,types,YES,101))return 3;
    puts("101-population legacy helper: bounded");return 0;
  }
  if (!strcmp(argv[1], "f4-boundaries")) {
    int data[4][2]={{3,9},{7,5},{4,8},{9,3}}, *counts[4];
    int quad[4]={0,1,2,3}, repeated[4]={0,1,0,1}, absent[4]={0,-1,2,3};
    double value; int ret;
    for (int i=0;i<4;++i) counts[i]=data[i];
    setfancyf4(YES);
    ret=getf4(counts,quad,&value);printf("ordinary %d %.12f\n",ret,value);
    ret=getf4(counts,repeated,&value);printf("overlap %d %.12f\n",ret,value);
    ret=getf4(counts,NULL,&value);printf("NULL %d %.12f\n",ret,value);
    ret=getf4(counts,absent,&value);printf("negative %d %.12f\n",ret,value);
    data[0][0]=data[0][1]=0;data[2][0]=data[3][0];data[2][1]=data[3][1];
    ret=getf4(counts,quad,&value);printf("fancy-zero %d %.12f\n",ret,value);
    setfancyf4(NO);ret=getf4(counts,quad,&value);printf("strict-missing %d %.12f\n",ret,value);
    for(int i=0;i<4;++i) data[i][0]=data[i][1]=INT_MAX;
    ret=getf4(counts,repeated,&value);printf("large-overlap %d %.12f\n",ret,value);
    data[0][0]=1;data[0][1]=0;
    ret=getf4(counts,repeated,&value);printf("one-overlap %d %.12f\n",ret,value);
    data[0][0]=3;data[0][1]=9;data[1][0]=1;data[1][1]=0;data[2][0]=4;data[2][1]=8;
    int partial[4]={0,1,0,2};
    ret=getf4(counts,partial,&value);printf("one-nonoverlap %d %.12f\n",ret,value);
    int second[4]={0,1,2,1};
    ret=getf4(counts,second,&value);printf("one-second-overlap %d %.12f\n",ret,value);
    return 0;
  }
  if (!strcmp(argv[1], "count-selection")) {
    Indiv people[2]={{0}}, *peopleptr[2]={&people[0],&people[1]};
    int genotype[2]={0,2},index[2]={0,1},types[2]={0,0},cells[2]={0,0};
    int *pop[1]={cells}, **counts[1]={pop}; SNP snp={0}, *snps[1]={&snp};
    packmode=NO;snp.gtypes=genotype;snp.ngtypes=2;snp.chrom=23;
    people[0].gender='F';people[0].hasxhets=YES;
    people[1].gender='M';people[1].ignore=YES;
    countpops(counts,snps,index,types,2,1);
    printf("raw indexed counts %d %d\n",cells[0],cells[1]);
    cells[0]=cells[1]=0;countpopsx(counts,snps,peopleptr,index,types,2,1);
    printf("ploidy-aware indexed counts %d %d\n",cells[0],cells[1]);
    cells[0]=cells[1]=0;snp.chrom=1;
    countpopsx(counts,snps,peopleptr,index,types,2,1);
    printf("autosomal indexed counts %d %d\n",cells[0],cells[1]);
    return 0;
  }
  if (!strcmp(argv[1], "ratio-lifetime") || !strcmp(argv[1], "block-upper") ||
      !strcmp(argv[1], "block-negative") || !strcmp(argv[1], "zero-rows") ||
      !strcmp(argv[1], "diff-zero-denominator") || !strcmp(argv[1], "diff-zero-se")) {
    int cells[6][5][2], *pop[6][5], **counts[6];
    int blocks[6]={0,0,1,2,2,2},top[4]={0,1,2,3},bot[4]={0,1,4,3};
    double est,sd;
    for (int s=0;s<6;++s) {
      counts[s]=pop[s];
      for (int p=0;p<5;++p) {
        cells[s][p][0]=1+p+(s%(p+2));cells[s][p][1]=12-cells[s][p][0];pop[s][p]=cells[s][p];
      }
      if (!strcmp(argv[1], "block-upper")) blocks[s]=3;
      if (!strcmp(argv[1], "block-negative")) blocks[s]=-1;
    }
    setfancyf4(YES);
    if (!strcmp(argv[1], "diff-zero-denominator") || !strcmp(argv[1], "diff-zero-se")) {
      int zero[4]={0,0,2,3};
      doq4ratdiff(&est,&sd,counts,blocks,1,6,
                 !strcmp(argv[1],"diff-zero-se")?zero:top,bot,zero,
                 !strcmp(argv[1],"diff-zero-denominator")?zero:bot,5,3);
      return 8;
    }
    for (int i=0;i<16;++i) {
      int used=doq4rat(&est,&sd,counts,blocks,!strcmp(argv[1],"zero-rows")?0:1,6,top,bot,5,3);
      if(used!=6 || !isfinite(est) || !isfinite(sd)) return 3;
      doq4ratdiff(&est,&sd,counts,blocks,1,6,top,bot,top,bot,5,3);
      if(!isfinite(est) || !isfinite(sd)) return 4;
    }
    puts("16 ratio/diff workspace lifetimes: finite");return 0;
  }
  return 2;
}
