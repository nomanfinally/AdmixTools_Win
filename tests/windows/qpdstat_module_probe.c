/* Direct, bounded probes of production functions; no production edits.
 * Include qpDstat to provide the ordinary tool globals and local mode routines.
 * Link its normal dependencies, excluding qpDstat.o. Each invocation is fresh:
 * process-global RNG/parser/hash state cannot contaminate another test.
 */
#include <admix_types.h>
#define main qpdstat_program_main
#include "../../src/qpDstat.c"
#undef main
#include <stddef.h>
#include <stdint.h>
#include <limits.h>
#include "../../src/geno.h"
#include "../../src/ldsubs.h"
#include "../../src/mapfile.h"
#ifdef _WIN32
#include <windows.h>
#else
#include <dirent.h>
#endif

static int handles(void) {
#ifdef _WIN32
  DWORD n=0;GetProcessHandleCount(GetCurrentProcess(),&n);return (int)n;
#else
  DIR *d=opendir("/proc/self/fd");int n=0;while(readdir(d))++n;closedir(d);return n;
#endif
}

static int packing(int normal)
{
  genotype_matrix matrix, readback;
  size_t i, j;
  genotype_matrix_initialize(&matrix);
  genotype_matrix_initialize(&readback);
  genotype_matrix_allocate(&matrix, normal ? 5 : 193, 65, !normal);
  for (i=0; i<genotype_matrix_num_samples(&matrix); ++i)
    for (j=0; j<65; ++j)
      genotype_matrix_set_genotype(&matrix, i, j, (char)((i+j)%4));
  genotype_matrix_set_individual_hash(&matrix, 123U);
  genotype_matrix_set_snp_hash(&matrix, 456U);
  for (int trans=0; trans<2; ++trans) {
    const char *name = trans ? "probe.tgeno" : "probe.geno";
    genotype_matrix_write_packed_file(&matrix, name, trans);
    genotype_matrix_read_file(&readback, name, O_RDONLY, NULL, NULL);
    if (genotype_matrix_get_individual_hash(&readback)!=123U ||
        genotype_matrix_get_snp_hash(&readback)!=456U) return 8;
    for (i=0; i<genotype_matrix_num_samples(&matrix); ++i)
      for (j=0; j<65; ++j)
        if (genotype_matrix_get_genotype(&readback,i,j)!=(i+j)%4) return 9;
    genotype_matrix_destructor(&readback);
    genotype_matrix_read_file_full(&readback, name, O_RDONLY, NULL, NULL);
    if (genotype_matrix_get_genotype(&readback,0,64)!=0) return 10;
    genotype_matrix_destructor(&readback);
  }
  genotype_matrix_destructor(&matrix);
  puts("packing/accessors/hashes/map/full-read/transpose: exact");
  return 0;
}

int main(int argc, char **argv)
{
  int i;
  if (argc<2) return 2;
  if (!strcmp(argv[1], "T04-banker-large")) {
    int types[101]={0}, quad[4]={97,98,99,100};
    types[97]=1; types[98]=types[99]=2;
    if (!islegal(quad,types,1,101)) return 4;
    puts("101-population banker selection: exact");
    return 0;
  }
  if (!strcmp(argv[1], "T04-tree-oracle")) {
    /* Known additive tree: pendants 1,2,3,4 and internal branch 5.
     * Relabel it through every permutation inside a five-population index. */
    double factors[6]={.5,.75,1,1,1.25,1.5}, distances[6]={3,9,10,10,11,7};
    int blocks[6]={0,1,2,3,4,5}, order[4], runs=0;
    double **f2=initarray_2Ddouble(10,6,0), **ab=initarray_2Ddouble(10,6,.5);
    ZALLOC(f2ind,25,int);
    for(int a=0,h=0;a<5;++a) for(int b=a+1;b<5;++b,++h)
      f2ind[a*5+b]=f2ind[b*5+a]=h;
    for(int a=1;a<=4;++a) for(int b=1;b<=4;++b) for(int c=1;c<=4;++c) for(int d=1;d<=4;++d) {
      if(a==b||a==c||a==d||b==c||b==d||c==d) continue;
      order[0]=a;order[1]=b;order[2]=c;order[3]=d;
      for(int u=0,h=0;u<4;++u) for(int v=u+1;v<4;++v,++h)
        for(int k=0;k<6;++k) f2[f2ind[order[u]*5+order[v]]][k]=distances[h]*factors[k];
      double z[5], lengths[5]; char actual[128];
      gettreelen(z,lengths,f2,ab,ab,6,order,5,blocks,6);
      snprintf(actual,sizeof(actual),"%.6f %.6f %.6f %.6f %.6f",lengths[0],lengths[1],lengths[2],lengths[3],lengths[4]);
      if(strcmp(actual,"1.000000 2.000000 5.000000 3.000000 4.000000")) { puts(actual); return 5; }
      ++runs;
    }
    free2D(&f2,10);free2D(&ab,10);free(f2ind);f2ind=NULL;
    printf("tree oracle: %d relabelings exact at six decimals\n",runs);
    return runs==24 ? 0 : 6;
  }
  if (!strcmp(argv[1], "M03-vector") && argc==3) {
    phandle *p=openpars(argv[2]);
    int a[3],b[3],n=0,nd=0; double x[3],y[3]; admix_long large=0;
    getints(p,"ints:",a,3); getintss(p,"ints:",b,&n);
    getdbls(p,"reals:",x,3); getdblss(p,"reals:",y,&nd);
    getlong(p,"large:",&large);closepars(p);
    if(n!=3||nd!=3||a[0]!=-2147483647-1||a[2]!=2147483647||large!=INT64_MAX) return 4;
    for(int k=0;k<3;++k) if(a[k]!=b[k]||x[k]!=y[k]) return 5;
    puts("vector/64-bit numeric parsing: exact");return 0;
  }
#ifdef _WIN32
  if (!strcmp(argv[1],"M01-sibling")) {
    const char *args[]={"plain","space value","quote\"inside","C:\\space\\","\xce\xb1","","end\\\\\"tail",NULL};
    int ret=admix_run_sibling("argv_child",args,"child.log");
    printf("sibling status: %d\n",ret);return ret;
  }
  if (!strcmp(argv[1],"M01-process-errors")) {
    const char *args[]={"--exit=7",NULL};
    printf("invalid name: %d\n",admix_run_sibling("../invalid",args,NULL));
    printf("missing child: %d\n",admix_run_sibling("t04_absent",args,NULL));
    printf("bad log: %d\n",admix_run_sibling("argv_child",args,"absent/child.log"));
    printf("child status: %d\n",admix_run_sibling("argv_child",args,"child.log"));
    return 0;
  }
  if (!strcmp(argv[1],"M01-services")) {
    FILE *f=fopen("lines","w");fputs("a\nlast",f);fclose(f);
    char *line=NULL;size_t capacity=0;f=fopen("lines","r");
    printf("getline: %lld\n",(long long)admix_getline(&line,&capacity,f));
    printf("getline: %lld\n",(long long)admix_getline(&line,&capacity,f));
    printf("getline: %lld\n",(long long)admix_getline(&line,&capacity,f));fclose(f);free(line);
    printf("bad getline: %lld\n",(long long)admix_getline(NULL,NULL,NULL));
    admix_setenv("T04_PROBE_ENV","one",1);admix_setenv("T04_PROBE_ENV","two",0);
    printf("env retained: %s\n",getenv("T04_PROBE_ENV"));
    admix_setenv("T04_PROBE_ENV","two",1);printf("env replaced: %s\n",getenv("T04_PROBE_ENV"));
    printf("bad env: %d\n",admix_setenv("bad=name","x",1));
    printf("copy: %d %d\n",admix_copy_file("lines","copied"),admix_copy_file("absent","copy-fail"));
    printf("filter: %d\n",admix_filter_fstats("parameters","filtered"));
    printf("diagnostic metrics: %d %d\n",admix_cpu_seconds()>=0,admix_memory_bytes()>0);
    return 0;
  }
#endif
  if (!strcmp(argv[1],"sample") && argc==6) {
    Indiv **people;
    char **pops;
    int count=getindivs(argv[2],&people), n=numlines(argv[3]);
    ZALLOC(pops,n,char *);
    n=loadlist(pops,argv[3]);
    setgk(people,count,argv[3],NULL,NULL);
    gkignore(people,count);
    SRAND((unsigned int)strtoul(argv[5],NULL,10));
    setplimit(people,count,pops,n,atoi(argv[4]));
    for (i=0;i<count;++i) if (!people[i]->ignore) printf("%d\n",i);
    return 0;
  }
  if (!strcmp(argv[1],"M01-io")) {
    unsigned char source[256], dest[256];
    FILE *f;
    for(i=0;i<256;++i) source[i]=(unsigned char)i;
    f=fopen("probe.bytes","w"); if(!f) return 3;
    if(fwrite(source,1,256,f)!=256 || fclose(f)) return 4;
    f=fopen("probe.bytes","r"); if(!f) return 5;
    size_t got=fread(dest,1,256,f); fclose(f);
    printf("text-mode-byte-roundtrip: %s %zu\n", got==256 && !memcmp(source,dest,256) ? "exact":"DIFF",got);
    return got==256 && !memcmp(source,dest,256) ? 0:6;
  }
  if (!strcmp(argv[1],"M02-strings")) {
    char input[]="  alpha\tbeta  gamma\n", *tokens[4];
    int n=splitup(input,tokens,4);
    printf("tokens: %d",n);
    for(i=0;i<n;++i) printf(" [%s]",tokens[i]);
    printnl(); freeup(tokens,n);
#ifndef T04_PRISTINE
    char *p=reserve_temp("t04-owned");
    if (!p || !file_exists(p)) return 3;
    release_temp(p,0);
    printf("temporary removed: %d\n",!file_exists(p));
    free(p);
#else
    puts("owned temporary extension absent in pristine upstream");
#endif
    return 0;
  }
  if (!strcmp(argv[1],"M03-parser") && argc==3) {
    phandle *p=openpars(argv[2]);
    int n=0; double x=0; char *s=NULL;
    dostrsub(p); getint(p,"integer:",&n); getdbl(p,"real:",&x); getstring(p,"file:",&s);
    printf("parsed: %d %.12f [%s]\n",n,x,s?s:"NULL");
    closepars(p); free(s); return 0;
  }
  if (!strcmp(argv[1],"M04-gauss") || !strcmp(argv[1],"M05-distributions")) {
    SRAND(77);
    for(i=0;i<32;++i) {
      if (argv[1][2]=='4') printf("gauss %d %.12f\n",i,gauss());
      else printf("distribution %d %.12f %.12f %.12f %.12f %d\n",i,
                  ranexp(),rangam(2.5),ranbeta(2,3),ranpoiss(4),ranbinom(20,.3));
    }
    return 0;
  }
  if (!strcmp(argv[1],"M04-reseed")) {
    SRAND(77); double first=gauss(); SRAND(77); double second=gauss();
    printf("reseed: %.12f %.12f\n",first,second);
    return 0;
  }
  if (!strcmp(argv[1],"M05-boundary")) {
    printf("bounds %.12f %.12f %d %.12f\n",rejnorm(2,2),uniform(4,4),ranbinom(0,.2),ranpoiss(0));
    return 0;
  }
  if (!strcmp(argv[1],"M06-sort")) {
    int values[64], order[64]; double data[8]={3,0,-1,0,3,2,-1,2}; int rank[8];
    for(i=0;i<64;++i) values[i]=i%4;
    isortit(values,order,64);
    for(i=0;i<64;++i) printf("sort: %d %d\n",values[i],order[i]);
    sortit(data,rank,8);
    for(i=0;i<8;++i) printf("double: %.0f %d\n",data[i],rank[i]);
    return 0;
  }
  if (!strcmp(argv[1],"M06-empty")) {int x=0;isortit(&x,&x,0);return 0;}
  if (!strcmp(argv[1],"M06-median-leak")) {
    double x[2]={1,3};printf("median %.12f %.12f\n",median(x,1),median(x,2));return 0;
  }
  if (!strcmp(argv[1],"M07-hash")) {
    int values[]={0,1,-1,INT_MIN,INT_MAX}; char *keys[]={"z","z","a"};
    for(i=0;i<5;++i) printf("hash %d %d %d %d\n",values[i],xhash1(values[i]),xhash2(values[i]),xshash(values[i]));
    printf("string %d %d %d\n",stringhash("Out"),fnv_hash("Out"),finddupalt(keys,3));
    xloadsearch(keys+1,2); printf("lookup %d %d\n",xfindit("a"),xfindit("absent"));
    xdestroy(); return 0;
  }
  if (!strcmp(argv[1],"M08-vector")) {
    double x[]={3000000000.,-3000000000.,1e12,2.5,-2.5}, y[5];
    admix_long rounded[5];
    fixitl(rounded,x,5);
    for(i=0;i<5;++i) printf("rounded: %" ADMIX_PRIdLONG "\n",rounded[i]);
    vclear(y,2,5); vvt(y,x,y,5); vvm(y,y,x,5);
    printf("vector %.12f %.12f %.12f\n",asum(y,5),vdot(x,y,5),asum2(y,5));
    printf("empty %.12f\n",asum(y,0)); return 0;
  }
  if (!strcmp(argv[1],"M09-jack") || !strcmp(argv[1],"M09-one")) {
    double j[]={.19,.21,.18,.22,0}, w[]={10,10,10,10,0}, est,sig;
    weightjack(&est,&sig,.2,j,w,!strcmp(argv[1],"M09-one")?1:5);
    printf("jack %.12f %.12f tails %.12f %.12f\n",est,sig,ntail(0),zprob(.5));
    return 0;
  }
  if (!strcmp(argv[1],"M10-solver") || !strcmp(argv[1],"M10-singular")) {
    double a[]={4,1,1,3},b[]={1,2},answer[2]={0}, inverse[4];
    if (!strcmp(argv[1],"M10-singular")) vzero(a,4);
    int status=solvit(a,b,2,answer);
    printf("solve %d %.12f %.12f\n",status,answer[0],answer[1]);
    if (status>=0) printf("inverse %.12f\n",pdinv(inverse,a,2));
    return 0;
  }
  if (!strcmp(argv[1],"M11-individuals") && argc==3) {
    Indiv **people; int n=getindivs(argv[2],&people);
    inddupcheck(people,n); printf("individuals: %d\n",n); return 0;
  }
  if (!strcmp(argv[1],"M12-packing")) return packing(0);
  if (!strcmp(argv[1],"M12-small-normal")) return packing(1);
  if (!strcmp(argv[1],"M12-overflow")) {
    genotype_matrix matrix;
    genotype_matrix_initialize(&matrix);
    genotype_matrix_allocate(&matrix,SIZE_MAX,2,true);
    genotype_matrix_destructor(&matrix); return 0;
  }
  if (!strcmp(argv[1],"M12-read") && argc==3) {
    genotype_matrix matrix;genotype_matrix_initialize(&matrix);
    int ret=genotype_matrix_read_file(&matrix,argv[2],0,NULL,NULL);
    if(ret<0 && (matrix.memory_map_start || matrix.genotypes || matrix.memory_map_length || matrix.num_rows || matrix.num_columns))
      return 9;
    printf("matrix status: %d\n",ret);genotype_matrix_destructor(&matrix);
    return ret<0 ? 1:0;
  }
  if (!strcmp(argv[1],"M12-map-leak")) {
    genotype_matrix matrix;FILE *f=fopen("empty.matrix","w");fclose(f);
    int before=handles(),ret=0;
    for(i=0;i<16;++i) ret=genotype_matrix_read_file(&matrix,"empty.matrix",0,NULL,NULL);
    printf("failed mappings: %d leaked handles: %d\n",ret,handles()-before);
    return 0;
  }
  if (!strcmp(argv[1],"M12-header-size")) {
    genotype_matrix matrix;char buffer[GENO_HEADER_SIZE];genotype_matrix_initialize(&matrix);
    matrix.transpose=true;matrix.num_rows=SIZE_MAX;matrix.num_columns=SIZE_MAX;
    matrix.individual_file_hash=UINT_MAX;matrix.snp_file_hash=UINT_MAX;
    genotype_matrix_header(&matrix,true,buffer);puts(buffer);return 0;
  }
  if (!strcmp(argv[1],"M12-write-missing")) {
    genotype_matrix matrix;genotype_matrix_initialize(&matrix);
    genotype_matrix_allocate(&matrix,1,1,true);
    genotype_matrix_write_packed_file(&matrix,"absent/probe.tgeno",true);
    genotype_matrix_destructor(&matrix);return 0;
  }
#ifndef _WIN32
  if (!strcmp(argv[1],"M12-write-full")) {
    genotype_matrix matrix;genotype_matrix_initialize(&matrix);
    genotype_matrix_allocate(&matrix,1,1,true);
    genotype_matrix_write_packed_file(&matrix,"/dev/full",true);
    genotype_matrix_destructor(&matrix);return 0;
  }
#endif
  if (!strcmp(argv[1],"M02-legacy-shell")) {
    char *p=runcmd("echo T04_probe");
    printf("legacy command produced file: %d\n",file_exists(p));
    if(file_exists(p))remove(p);free(p);return 0;
  }
  if (!strcmp(argv[1],"M13-map") && argc==3) {
    genFile *p=constructMap(argv[2],1,256,0);
    int ans=getgtypemap(p,0,3);
    destroyMap(p); printf("mapped packed element: %d\n",ans); return 0;
  }
  if (!strcmp(argv[1],"M14-bits")) {
    unsigned char bytes[16]={0};
    for(i=0;i<64;++i) wbuff(bytes,i,i%4);
    for(i=0;i<64;++i) if(rbuff(bytes,i)!=i%4) return 4;
    puts("64 packed elements exact"); return 0;
  }
  if (!strcmp(argv[1],"M17-fourier") && argc==3) {
    int n=atoi(argv[2]); double *j,*w,est,sig,rho;
    ZALLOC(j,n,double); ZALLOC(w,n,double);
    for(i=0;i<n;++i) {j[i]=.2+.01*(i%3);w[i]=1;}
    weightjackfourier(&est,&sig,.2,j,w,n,&rho);
    printf("fourier %.12f %.12f %.12f\n",est,sig,rho);free(j);free(w);return 0;
  }
  if (!strcmp(argv[1],"M18-list") && argc==3) {
    char *list[4]={0}; int types[4]={0}; int n=loadlist_type_capacity(list,argv[2],types,0,4);
    printf("list %d\n",n);for(i=0;i<n;++i){printf("%s %d\n",list[i],types[i]);free(list[i]);}return 0;
  }
  if (!strcmp(argv[1],"M18-file-leak")) {
    char *list[4]={0};int types[4]={0},before=handles();
    for(int run=0;run<16;++run){int n=loadlist_type_capacity(list,"types",types,0,4);for(i=0;i<n;++i)free(list[i]);}
    printf("list leaked handles: %d\n",handles()-before);return 0;
  }
  if (!strcmp(argv[1],"M19-ld") || !strcmp(argv[1],"M19-empty")) {
    double counts[]={10,2,1,2,20,3,1,3,10};
    if(!strcmp(argv[1],"M19-empty")) vzero(counts,9);
    printf("ld %.12f\n",lddip(counts)); printf("z %.12f\n",zdip(counts));return 0;
  }
  if (!strcmp(argv[1],"M20-regression") || !strcmp(argv[1],"M20-singular")) {
    double eq[]={1,0,1,1,1,2,1,3}, rhs[]={1,3,5,8}, ans[2]={0};
    if(!strcmp(argv[1],"M20-singular")) vzero(eq,8);
    double score=regressit(ans,eq,rhs,4,2);
    printf("regression %.12f %.12f %.12f\n",score,ans[0],ans[1]);return 0;
  }
  return 2;
}
