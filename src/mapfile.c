#include <admix_types.h>
/*
 * MapFile.c
 *
 *  Created on: Jun 21, 2021
 *      Author: Cokie; modified by Nick
 */

#include <stdio.h>
#include <stdlib.h>
#ifdef _WIN32
#include "win32/mman.h"
#else
#include <sys/mman.h>
#endif
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <assert.h>
#include <stdint.h>
#include <limits.h>
#include <errno.h>

#include "mapfile.h"
#include "admutils.h"  

// Memory mapping by Cokie Parke 

//function returns value of single 2-bit snp, given
//row and col location and genFile object containing data matrix
//return int value
int getgtypemap(genFile *data, int snpRow, int snpCol) 
{
	char* snps = data->snps;
        static admix_long ncall = 0 ;
        admix_long rowsize, offset ;
        char *buff ;  

        ++ncall ;
        rowsize = data -> rowSize ;  // rowsize is size of a row NOT number of rows 
        offset = data -> hdrSize ;  

        buff = snps + offset + snpRow*rowsize ;  // start of row  
        return rbuff((unsigned char *) buff, snpCol) ;   

} 

//memory maps file with given filename, returns
//genFile struct containing pointer representing file
genFile* constructMap(char* filename, admix_long numrows, admix_long rowSize, admix_long hdrSize) {
	genFile* geno;
        admix_long siz ;

	//open file to be mapped
	int mmfd = open(filename, O_RDONLY);

	if (mmfd <  0) fatalx("(constructMap) failure to open %s\n", filename) ;

	//get file length
	struct stat status;
	if (fstat(mmfd, &status) != 0) { close(mmfd); fatalx("fstat fails\n"); }
	admix_long fileLength = status.st_size;

        if (numrows < 0 || rowSize <= 0 || hdrSize < 0 ||
            numrows > INT_MAX || rowSize > INT_MAX || hdrSize > INT_MAX ||
            numrows > (ADMIX_LONG_MAX - hdrSize) / rowSize) {
          close(mmfd);
          fatalx("(constructMap) invalid genotype dimensions\n");
        }
	siz = numrows * rowSize + hdrSize ;
	if (siz <= 0 || (uint64_t)siz > SIZE_MAX || siz != fileLength) {
          close(mmfd);
          fatalx("(constructMqp) file size mismatch\n");
        }

	//memory map file
	void *mmfaddr = mmap(NULL, fileLength, PROT_READ, MAP_PRIVATE, mmfd, 0);
	if (mmfaddr == MAP_FAILED) {
                close(mmfd);
                fatalx("(constructMap) memory mapping failed: %s\n", filename);
	}

	//close file
	close(mmfd);

	//build genFile struct
	geno = malloc(sizeof(genFile));
        if (geno == NULL) {
          munmap(mmfaddr, (size_t)fileLength);
          fatalx("(constructMap) cannot allocate genotype mapping\n");
        }
	geno->colSize = (int)numrows ;
	geno->rowSize = (int)rowSize;
        geno -> hdrSize = (int)hdrSize ;
	geno->snps = (char*) mmfaddr;

        printf("mmfaddr: %p  fileLength: %" ADMIX_PRIdLONG "\n", geno -> snps, fileLength) ;;
        fflush(stdout) ;

	return geno;
}

//unmaps data file contained in given genFile struct
//frees dynamically allocated struct container
void destroyMap(genFile* data) {
	void* mmfaddr = (void*) data->snps;
	size_t fileLength = (size_t)data->colSize * data->rowSize + data -> hdrSize;
	munmap(mmfaddr, fileLength);
	free(data);
}
