#include <admix_types.h>
admix_long gcdx(admix_long a, admix_long b, admix_long *x, admix_long *y)
{
    admix_long x1, y1; // To store results of recursive call
    if (a == 0)
    {
        *x = 0;
        *y = 1;
        return b;
    }
 
 
    // Update x and y using results of recursive
    // call
    *x = y1 - (b/a) * x1;
    *y = x1;
 
    return gcdx(b%a, a, &x1, &y1) ;
}

// gcd = a*x + b*y 
