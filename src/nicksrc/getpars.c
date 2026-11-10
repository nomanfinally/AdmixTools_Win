#include <admix_types.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdarg.h>
#include <errno.h>
#include <limits.h>

#define MAXSTR  5000
#define MAXPARS 400

#include "nicklib.h"
#include "getpars.h"
#include "strsubs.h" 

/** 
 a simple keyword parameter cracker 
 comments with line starting #  
 syntax:  keyword param(s)   
 not designed to read large databases (needs hash code for that)
*/
void subcolon (char *ss);
void stripcomment (char *str);
int findpname (phandle * pp, char *parname);
int indxstring (char **ppars, int npars, char *ww);

static int parchange = 0;
static int debug = NO;

/* Retain the existing decimal syntax and floating conversion, but never
 * silently turn a malformed/out-of-range token into a scientific setting. */
static admix_long parse_integer(const char *text, const char *name, admix_long low, admix_long high)
{
  char *end;
  errno = 0;
  long long value = strtoll(text, &end, 10);
  if (errno == ERANGE || end == text || *end || value < low || value > high)
    fatalx("invalid integer parameter %s: %s\n", name, text);
  return (admix_long)value;
}

static double parse_real(const char *text, const char *name)
{
  char *end;
  errno = 0;
  double value = strtod(text, &end);
  if (end == text || *end || errno == ERANGE)
    fatalx("invalid real parameter %s: %s\n", name, text);
  /* NaN/Inf are syntactically real tokens. Scientific callers validate their
   * domain, rather than changing shared parser policy for unrelated tools. */
  return value;
}
static int readpars(phandle *pp, char *fname, char **ppars, char **pdata, int capacity, int depth);




int fixpars(phandle  *pp,  char *tag)  
{
  char  *sx ; 
  char **ppars, **pdata ; 
  int npars ;
  int k, x, t, a, nfix = 0  ; 
  char *wk,  *ww ;

  if (tag == NULL) return 0 ;

  ppars = pp -> ppars ; 
  pdata = pp -> pdata ; 
  npars = pp -> numpars ; 
  t = strlen(tag) ; 
  ZALLOC(wk, t+2, char) ;
  strcpy(wk, tag) ; strcat(wk, ":") ; 
  for (k=0; k<npars; ++k) { 
   sx = strstr(ppars[k], wk) ; 
   if (sx != ppars[k]) continue ; 
   sx = strchr(ppars[k], ':') ; 
   sx = sx+1 ; 
   a = indxstring (ppars, npars, sx) ;
   if (a>=0) ppars[a][0] = CNULL ; // delete old parameter

   ww = strdup(sx) ;
   strcpy(ww, sx) ;

   freestring(&ppars[k]) ; 
   ppars[k] = strdup (ww);
   freestring(&ww) ;
   ++nfix ;

  }

  free(wk) ;

  return nfix ;

}

int
readpars(phandle *pp, char *fname, char **ppars, char **pdata, int capacity, int depth)
{

  char *line = NULL;
  size_t linecap = 0;
  ssize_t linelen;
  int firstline = YES;
  char str[MAXSTR];
  char ww[MAXSTR];
  char rest[MAXSTR];

  int npars = 0, i;
  int len, plen, t;

  FILE *ff;

  if (depth >= 99) fatalx("+++ include files looping\n");

  ff = fopen (fname, "r");
  if (depth == 0) pp->fx = ff;
  if (ff == NULL) {
    perror ("(getpars) Can't open file \n");
    fatalx ("can't open %s\n", fname);
  }

  while ((linelen = getline(&line, &linecap, ff)) >= 0) {
    if (memchr(line, '\0', (size_t)linelen) != NULL)
      fatalx("NUL byte in parameter file %s; save as UTF-8 text\n", fname);
#ifdef _WIN32
    if (firstline && linelen >= 2 &&
        (((unsigned char)line[0] == 0xff && (unsigned char)line[1] == 0xfe) ||
         ((unsigned char)line[0] == 0xfe && (unsigned char)line[1] == 0xff)))
      fatalx("UTF-16 parameter file %s; save as UTF-8 text\n", fname);
    if (firstline && linelen >= 3 && !memcmp(line, "\xef\xbb\xbf", 3)) {
      memmove(line, line + 3, (size_t)linelen - 2);
      linelen -= 3;
    }
#endif
    firstline = NO;
    if (linelen >= MAXSTR - 1) fatalx("parameter line too long in %s\n", fname);

    len = strlen (line);

    /* Consume both bytes of CRLF before storing macro values. */
    while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r'))
      line[--len] = '\0';

    if (first_word (line, ww, rest) > 0) {

      if (ww[0] == '#')
        continue;
      /*AT: 12/2/04: Adding check to make sure that the parameter name ends in : */
      t = strcmp(ww, "+++") ; 
      if (t==0) { 
        stripcomment (rest);
        striptrail (rest, ' ');   /* no trailing blanks */
        npars += readpars(pp, rest, ppars+npars, pdata+npars, capacity-npars, depth+1);
        continue ;
      }
      plen = strlen (ww);
      if (ww[plen - 1] != ':')
        printf
          ("**warning: dubious parameter, please check the parameter name %s\n",
           ww);
      t = indxstring (ppars, npars, ww);
      if (t >= 0)
        fatalx ("duplicate parameter: %s\n", ww);
      if (npars >= capacity) fatalx("too many parameters (maximum %d)\n", MAXPARS);
      ppars[npars] = strdup (ww);
      stripcomment (rest);
      striptrail (rest, ' ');   /* no trailing blanks */
      pdata[npars] = strdup (rest);
      ++npars;

      if (debug)
        printf ("param %d %s %s\n", npars, ppars[npars - 1],
                pdata[npars - 1]);

    }
  }


  if (ferror(ff)) fatalx("error reading parameter file %s\n", fname);
  free(line);
  if (depth > 0) fclose(ff);
  return npars ;


}

phandle *
openpars (char *fname)

/* constructor */
{
  phandle *pp;

  char *ppars[MAXPARS];
  char *pdata[MAXPARS];

  int npars = 0, i;

  pp = (phandle *) malloc (sizeof (phandle));

  npars = readpars(pp, fname, ppars, pdata, MAXPARS, 0);
  for (i = 0; i < npars; ++i)
    if (indxstring(ppars, i, ppars[i]) >= 0)
      fatalx("duplicate parameter: %s\n", ppars[i]);
  pp->numpars = npars;

    if (npars>MAXPARS) fatalx("too many parameters: %d\n", npars) ;
    ZALLOC (pp->ppars, MAXPARS, char *);
    ZALLOC (pp->pdata, MAXPARS, char *);
  if (npars == 0)  {
    fprintf (stderr, "***warning: no parameters in %s\n", fname);
  }


  for (i = 0; i < npars; i++) {

    pp->ppars[i] = strdup (ppars[i]);
    pp->pdata[i] = strdup (pdata[i]);
    striplead(pp -> pdata[i], ' ') ;
//  printf("zz: %d %s %s\n",i,ppars[i],pp->ppars[i]) ; 

  }

  for (i = 0; i < npars; i++) {
    free (ppars[i]);
    free (pdata[i]);
  }

  return pp;

}

void
closepars (phandle * pp)

/* destructor */
{
  int n, i;

  fclose (pp->fx);
  n = pp->numpars;
  for (i = 0; i < n; i++) {
    free (pp->ppars[i]);
    free (pp->pdata[i]);
  }

  free (pp->ppars);
  free (pp->pdata);

  free (pp);
  pp = NULL;


}

void
stripcomment (char *str)
{
  int i, len;
#ifdef _WIN32
  int quoted = NO;
#endif

  len = strlen (str);

  for (i = 0; i < len; i++) {
#ifdef _WIN32
    if (str[i] == '"') quoted = !quoted;
    if (quoted) continue;
#endif
    if (str[i] == '#') {
      str[i] = '\0';
      return;
    }
  }
}

#define MAXFIELD 1000

int
getlongstring (phandle * pp, char *parname, char **strng)
// whole of line
{

  char *field[MAXFIELD];
  int n, kode;

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  *strng = strdup (pp->pdata[kode]);
  return 1;
}


int
getstring (phandle * pp, char *parname, char **strng)
{

  char *field[MAXFIELD];
  int n, kode;

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
#ifdef _WIN32
  /* Quoting accommodates native Windows paths with spaces. Unquoted values
   * retain upstream's first-token semantics. */
  if (pp->pdata[kode][0] == '"') {
    char *end = strchr(pp->pdata[kode] + 1, '"');
    if (end == NULL) fatalx("unterminated quoted parameter: %s\n", parname);
    if (end == pp->pdata[kode] + 1) fatalx("empty parameter: %s\n", parname);
    {
      size_t length = (size_t)(end - pp->pdata[kode] - 1);
      *strng = malloc(length + 1);
      if (*strng == NULL) fatalx("Unable to allocate parameter string\n");
      memcpy(*strng, pp->pdata[kode] + 1, length);
      (*strng)[length] = '\0';
      return 1;
    }
  }
#endif
  n = splitup (pp->pdata[kode], field, MAXFIELD);
  if (n == 0) fatalx("empty parameter: %s\n", parname);
  *strng = strdup (field[0]);
  freeup (field, n);
  return 1;
}


int
getint (phandle * pp, char *parname, int *kret)
{

  char *field[MAXFIELD];
  char str[MAXSTR];
  int n, kode;

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  n = splitup (pp->pdata[kode], field, MAXFIELD);
  if (n == 0) fatalx("empty parameter: %s\n", parname);
  strcpy (str, field[0]);
  freeup (field, n);
  if (strcmp (str, "YES") == 0) {
    *kret = YES;
    return 1;
  }
  if (strcmp (str, "NO") == 0) {
    *kret = NO;
    return 1;
  }

  if (strcmp (str, "yes") == 0) {
    *kret = YES;
    return 1;
  }
  if (strcmp (str, "no") == 0) {
    *kret = NO;
    return 1;
  }

  *kret = (int)parse_integer(str, parname, INT_MIN, INT_MAX);
  return 1;
}

int
getlong (phandle * pp, char *parname, admix_long *kret)
{

  char *field[MAXFIELD];
  char str[MAXSTR];
  int n, kode;

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  n = splitup (pp->pdata[kode], field, MAXFIELD);
  if (n == 0) fatalx("empty parameter: %s\n", parname);
  strcpy (str, field[0]);
  freeup (field, n);
  if (strcmp (str, "YES") == 0) {
    *kret = YES;
    return 1;
  }
  if (strcmp (str, "NO") == 0) {
    *kret = NO;
    return 1;
  }

  *kret = parse_integer(str, parname, INT64_MIN, INT64_MAX);
  return 1;
}


int
getints (phandle * pp, char *parname, int *aint, int nint)
{
  char *field[MAXFIELD];
  int n, kode, i;
  char str[MAXSTR];

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;

  strcpy (str, pp->pdata[kode]);
  subcolon (str);
  n = splitup (str, field, MAXFIELD);

  if (nint < n)
    fatalx ("(getints) wrong number of ints in line\n");

  for (i = 0; i < n; i++) {
    aint[i] = (int)parse_integer(field[i], parname, INT_MIN, INT_MAX);
  }
  freeup (field, n);
  return n;
}

int
getintss (phandle * pp, char *parname, int *aint, int *xint)

/* white space separated */
{
  char *field[MAXFIELD];
  int n, kode, i;
  char str[MAXSTR];

  *xint = 0;
  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  strcpy (str, pp->pdata[kode]);
  subcolon (str);
  n = splitup (str, field, MAXFIELD);
  for (i = 0; i < n; i++) {
    aint[i] = (int)parse_integer(field[i], parname, INT_MIN, INT_MAX);
  }
  freeup (field, n);
  *xint = n;
  return 1;
}

int
getdbls (phandle * pp, char *parname, double *dbl, int ndbl)
{
  char *field[MAXFIELD];
  int n, kode, i;
  char str[MAXSTR];

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  strcpy (str, pp->pdata[kode]);
  subcolon (str);
  n = splitup (str, field, MAXFIELD);
  if (ndbl != n)
    fatalx ("(getdbls) wrong number of dbls in line\n");
  for (i = 0; i < n; i++) {
    dbl[i] = parse_real(field[i], parname);
  }
  freeup (field, n);
  return 1;
}

int
getdblss (phandle * pp, char *parname, double *dbl, int *ndbl)

/* separated no check */
{
  char *field[MAXFIELD];
  int n, kode, i;
  char str[MAXSTR];

  *ndbl = 0;
  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  strcpy (str, pp->pdata[kode]);
  subcolon (str);
  n = splitup (str, field, MAXFIELD);
  for (i = 0; i < n; i++) {
    dbl[i] = parse_real(field[i], parname);
  }
  freeup (field, n);
  *ndbl = n;
  return 1;
}

void
subcolon (char *ss)

/* substitute ' ' for ':' or ',' */
{
  int i, l;
  l = strlen (ss);
  for (i = 0; i < l; i++) {
    if (ss[i] == ':')
      ss[i] = ' ';
    if (ss[i] == ',')
      ss[i] = ' ';
  }
}


int
getdbl (phandle * pp, char *parname, double *dbl)
{
  char *field[MAXFIELD];
  int n, kode;

  kode = findpname (pp, parname);
  if (kode < 0)
    return kode;
  n = splitup (pp->pdata[kode], field, MAXFIELD);
  if (n == 0) fatalx("empty parameter: %s\n", parname);
  *dbl = parse_real(field[0], parname);
  freeup (field, n);
  return 1;
}

int
findpname (phandle * pp, char *parname)
{
  int k;

  for (k = 0; k < pp->numpars; k++) {
    if (strcmp (parname, pp->ppars[k]) == 0)
      return k;
  }
  return -1;
}

void
writepars (phandle * pp)
{
  int k;
  if (pp == NULL)
    fatalx ("(writepars) phandle not open\n");
  for (k = 0; k < pp->numpars; k++) {
    if (pp->ppars[k][0] == CNULL) continue ;
    printf ("%s %s\n", pp->ppars[k], pp->pdata[k]);
  }
  fflush(stdout) ; 
}

void
fwritepars (FILE * fff, phandle * pp)
{
  int k;
  if (pp == NULL)
    fatalx ("(writepars) phandle not open\n");
  for (k = 0; k < pp->numpars; k++) {
    fprintf (fff, "%s %s\n", pp->ppars[k], pp->pdata[k]);
  }
}


void
dostrsub (phandle * pp)
{

/** 
 massage phandle data structure  
 to do string substitutions of 
 UPPER case paramewters
*/

  int n, nu, nl;
  int *isupp, *islow, *slenm, *indx;
  int i, j, k, l, ind;
  int nchange = 0;
  char *inx, *outx;
  n = pp->numpars;

  ZALLOC (isupp, n, int);
  ZALLOC (islow, n, int);
  ZALLOC (slenm, n, int);
  ZALLOC (indx, n, int);

  nu = nl = 0;
  for (k = 0; k < pp->numpars; k++) {
    if (upstring (pp->ppars[k])) {
      isupp[nu] = k;
      l = strlen (pp->ppars[k]);
      slenm[nu] = -(10000 * l - k);

/** 
 after sorting longest first then order in file
 ensures sort is stable
*/

      ++nu;
    }
    else {
      islow[nl] = k;
      ++nl;
    }
  }
  if (nu == 0)
    return;
  isortit (slenm, indx, nu);
  for (i = 0; i < nu; i++) {
    ind = indx[i];
    k = isupp[ind];
    inx = strdup (pp->ppars[k]);
    l = strlen (inx);
    if (inx[l - 1] == ':')
      inx[l - 1] = '\0';
    outx = strdup (pp->pdata[k]);
    for (j = 0; j < nl; j++) {
      k = islow[j];
      nchange += substring (&(pp->pdata[k]), inx, outx);
      if (nchange > 0)
        break;
    }
    free (inx);
    free (outx);
  }
  free (isupp);
  free (islow);
  free (slenm);
  free (indx);

  parchange += nchange;
  if (parchange > 10000)
    fatalx ("(getpars) dostrsub looping\n");
  if (nchange > 0)
    dostrsub (pp);

}

  
void mkparamfile(char *logfile, char *outparams) 
{
  FILE *fff, *fout ; 
  char line[MAXSTR+1] ;
  int sw = 0 ; 

  openit(outparams, &fout, "w") ;
  openit(logfile, &fff, "r") ;

  while (fgets(line, MAXSTR, fff) != NULL)  {
   if ((sw==0) && (strstr(line, "###start: params") != NULL)) { 
    sw = 1 ; 
    continue ; 
   } 
   if ((sw==1) && (strstr(line, "###end: params") != NULL)) { 
    sw = 2 ; 
    break ;
   } 
   fprintf(fout, "%s", line) ;
  }

  fclose(fout) ;
  fclose(fff) ;

}

void writeparsx (phandle * pp)
{
  int k;
  if (pp == NULL)
    fatalx ("(writeparsx) phandle not open\n");

  printf("###start: params\n") ;

  for (k = 0; k < pp->numpars; k++) {
    printf ("%s %s\n", pp->ppars[k], pp->pdata[k]);
  }
  printf("###end: params\n") ;
  fflush(stdout) ;
}


