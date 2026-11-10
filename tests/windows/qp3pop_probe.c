/* Production qp3Pop functions, ordinary link dependencies, fresh process per case. */
#define main qp3pop_program_main
#include "../../src/qp3Pop.c"
#undef main
#undef Y
#undef E
#undef A
extern int packmode;
#include <signal.h>
#ifdef _WIN32
#include <windows.h>
#include <io.h>
#else
#include <dirent.h>
#endif

static int handles(void) {
#ifdef _WIN32
  DWORD n=0; GetProcessHandleCount(GetCurrentProcess(), &n); return (int)n;
#else
  DIR *d=opendir("/proc/self/fd"); int n=0;
  while(readdir(d)) ++n; closedir(d); return n;
#endif
}

static void setup(int n) {
  packmode=NO;
  numindivs=n;
  ZALLOC(indivmarkers,n,Indiv *);
  for(int i=0;i<n;++i) {
    ZALLOC(indivmarkers[i],1,Indiv);
    indivmarkers[i]->egroup=strdup(i%3==0?"A":i%3==1?"B":"X");
    indivmarkers[i]->hasxhets=YES;
    sprintf(indivmarkers[i]->ID,"I%d",i);
  }
  setindm(indivmarkers);
}

int main(int argc,char **argv) {
  if(argc!=2) return 2;
  if(!strcmp(argv[1],"details-write-failure")) {
    int fds[2],index=0,type=0; double est,sd;
#ifdef _WIN32
    if(_pipe(fds,4096,_O_BINARY)!=0) return 2;
    _close(fds[0]);snpdetailsfile=_fdopen(fds[1],"w");
#else
    if(pipe(fds)!=0) return 2;
    close(fds[0]);signal(SIGPIPE,SIG_IGN);snpdetailsfile=fdopen(fds[1],"w");
#endif
    if(!snpdetailsfile || setvbuf(snpdetailsfile,NULL,_IOFBF,4096)!=0) return 2;
    snpdetailsname="closed details pipe";
    fputs("buffered detail bytes\n",snpdetailsfile);
    dof3score(&est,&sd,NULL,&index,&type,1,0,3,12);
    return 0;
  }
  if(!strcmp(argv[1],"early-return")) {
    double est,sd; int index=0,type=0, before;
    snpdetailsname="details.out";
    before=handles();
    for(int i=0;i<16;++i)
      if(dof3score(&est,&sd,NULL,&index,&type,1,0,3,12)!=-1) return 3;
    printf("extra open handles: %d\n",handles()-before);
    return 0;
  }
  if(!strncmp(argv[1],"sampling-",9)) {
    char *pops[]={"A","B","X","C"};
    char *all[]={"Out","A","B","C","X","R1","R2","R3","R4"};
    setup(54);
    for(int i=0;i<54;++i) {
      free(indivmarkers[i]->egroup);
      indivmarkers[i]->egroup=strdup(all[i/6]);
      indivmarkers[i]->ignore=(i<6 || i>=30);
    }
    SRAND((unsigned int)strtoul(argv[1]+9,NULL,10));
    setplimit(indivmarkers,numindivs,pops,4,3);
    for(int i=0;i<numindivs;++i) if(!indivmarkers[i]->ignore) printf("%d\n",i);
    return 0;
  }
  if(!strcmp(argv[1],"jackknife")) {
    double top[]={1,2,4,3},bot[]={3,4,5,6},wt[]={2,3,4,5},est,sd;
    setjquart(NO,YES,-1);
    estjackq(&est,&sd,top,bot,wt,4);
    printf("%.12f %.12f\n",est,sd);return 0;
  }
  if(!strncmp(argv[1],"jack-",5)) {
    double top[]={1,2,4,3},bot[]={3,4,5,6},wt[]={2,3,4,5},est,sd;
    double q=!strcmp(argv[1],"jack-half")?.5:!strcmp(argv[1],"jack-nan")?NAN:.49;
    setjquart(NO,YES,q);estjackq(&est,&sd,top,bot,wt,4);
    return 0; /* Reaching this line must fail the expected-rejection check. */
  }
  if(!strcmp(argv[1],"negative-type") || !strcmp(argv[1],"upper-type") || !strncmp(argv[1],"inbreed-large",13) || !strcmp(argv[1],"f3-boundaries")) {
    int large=!strncmp(argv[1],"inbreed-large",13);
    int mixed=!strcmp(argv[1],"inbreed-large-x");
    int n=large?150000:6;
    SNP snp={0}; int *index,*types; double top,bot;
    setup(n); ZALLOC(index,n,int);ZALLOC(types,n,int);ZALLOC(snp.gtypes,n,int);
    snp.ngtypes=n;snp.chrom=1;
    for(int i=0;i<n;++i) {
      index[i]=i;types[i]=i%3;snp.gtypes[i]=(i/3)%2?2:0;
      if(mixed) indivmarkers[i]->hasxhets=((i/3)%4<2);
    }
    if(mixed) snp.chrom=23;
    setinbreed(large);
    if(!strcmp(argv[1],"negative-type")) types[0]=-1;
    if(!strcmp(argv[1],"upper-type")) types[0]=3;
    if(!strcmp(argv[1],"f3-boundaries")) {
      for(int i=0;i<n;++i) snp.gtypes[i]=1;
      int ret=f3sc(&top,&bot,&snp,indivmarkers,index,types,n,2,0,1);
      printf("heterozygous ret=%d top=%.12f bot=%.12f\n",ret,top,bot);
      for(int i=0;i<n;++i) snp.gtypes[i]=-1;
      ret=f3sc(&top,&bot,&snp,indivmarkers,index,types,n,2,0,1);
      printf("missing ret=%d top=%.12f bot=%.12f\n",ret,top,bot);
    } else {
      int ret=f3sc(&top,&bot,&snp,indivmarkers,index,types,n,2,0,1);
      printf("ret=%d top=%.12f bot=%.12f\n",ret,top,bot);
      if(!strcmp(argv[1],"negative-type") || !strcmp(argv[1],"upper-type")) {
        double expected_top,expected_bot;
        int expected_ret=f3sc(&expected_top,&expected_bot,&snp,indivmarkers,index+1,types+1,n-1,2,0,1);
        if(ret!=expected_ret || top!=expected_top || bot!=expected_bot) return 5;
        puts("invalid type skipped exactly like a physically omitted row");
      }
      if(mixed) {
        double h=37500.0*37500.0/(75000.0*75000.0-125000.0);
        printf("expected top=%.12f bot=%.12f\n",.25-h,2*h);
      }
      else if(large) printf("expected top=%.12f bot=%.12f\n",-.5/99998.,50000./99998.);
    }
    return 0;
  }
  return 2;
}
