# TinyEXR 3

This recipe packages the hosted C11 API in `exr.h`, with library `tinyexr3` and
CMake target `tinyexr::tinyexr`. It does not package the deprecated C++ v1 API;
use `tinyexr/1.0.13` for that interface.

Zstandard and the optional libdeflate backend are supplied by Conan rather than
compiled from bundled copies. `with_libdeflate=True` follows upstream's hosted
default; set it to `False` to use TinyEXR's own DEFLATE implementation.
`with_thread=True` enables upstream's C11-thread/GCD codec parallelism.

The package includes the standard CPU codecs and hosted I/O. Upstream's optional
CUDA/Vulkan acceleration and freestanding build modes are not enabled.
MSVC builds use `/experimental:c11atomics` because the codec uses C11 atomic
function pointers. The MSVC bit-scan patch preserves the HTJ2K decoder's
highest-set-bit operation using the corresponding native intrinsic.

The consumer test checks both C and C++ linkage and lossless ZIP, PIZ,
Zstandard, and HTJ2K encode/decode round trips through the packaged library.
