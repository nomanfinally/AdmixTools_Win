/* Independent convex objective for the unchanged production GSL bridge. */
#include <stdio.h>
#include <math.h>
int gsldetails=0;
double gslprecision=1e-9;
int gslsetup(int n, double *p);
double gslopt(double *p);
double scorit(double *p, int n, double *fix, double *ans)
{
  double a=p[0]-.25, b=p[2]-.75;
  return a*a+2*b*b;
}
int main(void)
{
  double p[2]={.1,.9};
  if (gslsetup(0,p)!=0 || gslsetup(2,p)!=1) return 2;
  double q=gslopt(p);
  printf("optimum %.12f %.12f %.12f\n",p[0],p[1],q);
  return fabs(p[0]-.25)<1e-7 && fabs(p[1]-.75)<1e-7 && q<1e-14 ? 0:3;
}
