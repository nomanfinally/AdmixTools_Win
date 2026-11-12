/* Fault-injection child: valid output followed by a nonzero exit status. */
#include <stdio.h>
#include <string.h>
int main(int argc, char **argv)
{
  char line[4096], output[4096], data[8192];
  FILE *par, *in, *out;
  size_t n;
  if (argc!=3 || strcmp(argv[1],"-p")) return 2;
  par=fopen(argv[2],"r"); if (!par) return 3;
  output[0]=0;
  while (fgets(line,sizeof(line),par)) {
    if (strncmp(line,"fstatsoutname:",14)) continue;
    char *p=line+14;
    while (*p==' ' || *p=='\t') ++p;
    if (*p=='"') ++p;
    snprintf(output,sizeof(output),"%s",p);
    output[strcspn(output,"\"\r\n")]=0;
  }
  fclose(par);
  in=fopen("input.fstats","rb"); out=fopen(output,"wb");
  if (!in || !out) return 4;
  while ((n=fread(data,1,sizeof(data),in))) if(fwrite(data,1,n,out)!=n) return 5;
  fclose(in); if(fclose(out)) return 6;
  fputs("fixture qpfstats exit 7\n",stderr);
  return 7;
}
