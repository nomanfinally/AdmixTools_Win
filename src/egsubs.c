#include  "mcio.h"
#include  "egsubs.h"
#include <errno.h>
#include <limits.h>


int
makeeglist (char **eglist, int maxnumeg, Indiv ** indivmarkers, int numindivs)
// old routine mkeglist  
{

  Indiv *indx;
  int i, k, numeg = 0;
  for (i = 0; i < numindivs; i++) {
    indx = indivmarkers[i];
    if (indx->ignore)
      continue;
    k = indxindex (eglist, numeg, indx->egroup);
    if (k < 0) {
      if (numeg >= maxnumeg) {
	printf
	  ("number of populations too large.  Increase maxpops if you wish\n");
	fatalx
	  ("(makeeglist) You really want to analyse more than %d populations?\n",
	   maxnumeg);
      }
      eglist[numeg] = strdup (indx->egroup);
      ++numeg;
    }
  }
  return numeg;
}

int
mkeglist (Indiv ** indm, int numindivs, char **eglist)
{
  Indiv *indx;
  int i, k, numeg = 0;
  for (i = 0; i < numindivs; i++) {
    indx = indm[i];
    if (indx->ignore)
      continue;
    k = indxindex (eglist, numeg, indx->egroup);
    if (k < 0) {
      eglist[numeg] = strdup (indx->egroup);
      ++numeg;
    }
  }
  return numeg;
}

int
loadlist_type (char **list, char *listname, int *ztypes, int off)
{
  /* Legacy interface: callers must supply space for every input row. */
  return loadlist_type_capacity(list, listname, ztypes, off, INT_MAX);
}

int
loadlist_type_capacity (char **list, char *listname, int *ztypes, int off, int capacity)
// listname is just a list of names ... 
{
  FILE *lfile;
  char line[MAXSTR];
  char *spt[MAXFF];
  char *sx;
  Indiv *indx;
  int nsplit, i, n = 0, tt;

  if (listname == NULL)
    return 0;
  openit (listname, &lfile, "r");
  while (fgets (line, MAXSTR, lfile) != NULL) {
    nsplit = splitup (line, spt, MAXFF);
    if (nsplit == 0)
      continue;
    sx = spt[0];
    if (sx[0] == '#') {
      freeup (spt, nsplit);
      continue;
    }
    if (nsplit < 2)
      fatalx ("bad listname: %s\n", sx);
    if (n >= capacity) fatalx("typed population list exceeds capacity %d\n", capacity);
    char *end;
    long value;
    errno = 0;
    value = strtol(spt[1], &end, 10);
    if (errno || end == spt[1] || *end || value < INT_MIN || value > INT_MAX ||
        (int64_t)value + off < INT_MIN || (int64_t)value + off > INT_MAX)
      fatalx("invalid population type: %s\n", spt[1]);
    list[n] = strdup (sx);
    ztypes[n] = (int)value + off;
    ++n;
    freeup (spt, nsplit);
  }
  fclose(lfile);
  return n;
}


void
seteglist (Indiv ** indm, int nindiv, char *eglistname)
{
  FILE *egfile;
  char line[MAXSTR];
  char *spt[MAXFF];
  char *sx;
  Indiv *indx;
  int nsplit, i;

  if (eglistname == NULL)
    return;
  openit (eglistname, &egfile, "r");
  while (fgets (line, MAXSTR, egfile) != NULL) {
    nsplit = splitup (line, spt, MAXFF);
    if (nsplit == 0)
      continue;
    sx = spt[0];
    if (sx[0] == '#')
      continue;
    setstatus (indm, nindiv, sx);
    freeup (spt, nsplit);
  }
  fclose (egfile);
}

void
seteglistv (Indiv ** indm, int nindiv, char *eglistname, int val)
{
  FILE *egfile;
  char line[MAXSTR];
  char *spt[MAXFF];
  char *sx = NULL;
  Indiv *indx;
  int nsplit, i;

  if (eglistname == NULL) {
    setstatusv (indm, nindiv, NULL, val);
  }

  openit (eglistname, &egfile, "r");
  while (fgets (line, MAXSTR, egfile) != NULL) {
    nsplit = splitup (line, spt, MAXFF);
    if (nsplit == 0)
      continue;
    sx = spt[0];
    if (sx[0] == '#')
      continue;
    setstatusv (indm, nindiv, sx, val);
    freeup (spt, nsplit);
  }
  fclose (egfile);
}
