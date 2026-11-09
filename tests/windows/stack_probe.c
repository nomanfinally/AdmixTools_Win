/* Exercise more than MinGW's default 2 MiB, within the Linux 8 MiB allowance.
 * Volatile page touches prevent the compiler from removing the stack storage.
 */
#include <stdio.h>
#include <stddef.h>

static unsigned int __attribute__((noinline)) touch_stack(void)
{
    volatile unsigned char pages[4 * 1024 * 1024];
    size_t i;
    unsigned int sum = 0;
    for (i = 0; i < sizeof(pages); i += 4096)
        pages[i] = (unsigned char)(i / 4096);
    for (i = 0; i < sizeof(pages); i += 4096)
        sum += pages[i];
    return sum;
}

int main(void)
{
    unsigned int sum = touch_stack();
    printf("stack bytes: 4194304 checksum: %u\n", sum);
    return sum == 130560 ? 0 : 1;
}
