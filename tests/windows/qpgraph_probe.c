/* Exercise production graph paths and constrained fitting without changing them. */
#define main qpgraph_program_main
#include "../../src/qpGraph.c"
#undef main

int main(int argc, char **argv)
{
  if (argc != 2) return 2;
  if (!strcmp(argv[1], "solve")) {
    double q[9]={1,0,0,0,1,0,0,0,1};
    double p[6]={1,0,0,1,1,1}, rhs[3]={2,3,5}, ans[2], score;
    int zero[2]={0,0};
    ezero=zero; diag=0;
    score=calcxx(ans,q,p,rhs,3,2,1);
    printf("interior %.12f %.12f %.12f\n",ans[0],ans[1],score);
    rhs[0]=-1; rhs[1]=3; rhs[2]=2;
    score=calcxx(ans,q,p,rhs,3,2,1);
    printf("boundary %.12f %.12f %.12f\n",ans[0],ans[1],score);
    return 0;
  }
  for (int repeat=0; repeat<(!strcmp(argv[1],"lifetime")?16:1); ++repeat) {
    char *names[MAXG];
    double pw[MAXG*MAXG]={0}, aw[MAXG*MAXG]={0};
    int rows,edges,ancestors,n;
    loadgraph("graph",NULL);
    if (!strcmp(argv[1],"simplify")) gsimplify(0);
    if (!strcmp(argv[1],"delete")) { dellabel("X"); gsimplify(0); }
    getpops(names,&n);
    getpwts(pw,aw,&rows,&edges,&ancestors);
    printf("graph %d %d %d %d\n",n,rows,edges,ancestors);
    for (int i=0;i<rows;++i) {
      printf("%s-%s",names[i+1],names[0]);
      for(int j=0;j<edges;++j) printf(" %.12f",pw[i*edges+j]);
      for(int j=0;j<ancestors;++j) printf(" a:%.12f",aw[i*ancestors+j]);
      puts("");
    }
    freeup(names,n);
    freegraph();
  }
  return 0;
}
