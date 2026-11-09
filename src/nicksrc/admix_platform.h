#ifndef ADMIXTOOLS_PLATFORM_H
#define ADMIXTOOLS_PLATFORM_H
#ifdef _WIN32
#define ADMIX_VERSION_SUFFIX ".w"
#define ADMIX_PARAMETER_PATH "\"%s\""
#else
#define ADMIX_VERSION_SUFFIX ""
#define ADMIX_PARAMETER_PATH "%s"
#endif
#endif
