#include "admutils.h"  


int makeeglist(char **eglist, int maxnumeg, Indiv **indivmarkers, int numindivs)  ; 
int mkeglist(Indiv **indm, int numindivs, char **eglist) ;
void seteglist(Indiv **indm, int nindiv, char *eglistname)  ;
void seteglistv(Indiv **indm, int nindiv, char *eglistname, int val) ;
int loadlist(char **list,  char *listname)  ;
/* Legacy interface requires arrays large enough for every non-comment row.
 * Use the capacity interface for caller-owned fixed-size arrays. */
int  loadlist_type(char **list, char *listname, int *ztypes, int off)   ;
int loadlist_type_capacity(char **list, char *listname, int *ztypes, int off, int capacity);
