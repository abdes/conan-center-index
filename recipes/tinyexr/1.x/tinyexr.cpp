#if defined(_WIN32) && !defined(NOMINMAX)
#define NOMINMAX
#endif

#if !TINYEXR_USE_MINIZ
#include <zlib.h>
#endif

#define TINYEXR_IMPLEMENTATION
#include <tinyexr.h>
