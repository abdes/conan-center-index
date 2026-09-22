# TinyEXR 1.0.13

This recipe builds the legacy C++ API as a library and retains the existing
`with_z`, `with_piz`, `with_zfp`, `with_thread`, and `with_openmp` options.
Older releases keep their existing recipe in `all`.

The exported CMake build uses Conan's compression dependencies and applies the
selected options to the library itself. Upstream's root CMake project is a
compile-test project that builds bundled miniz and does not implement all these
options. The consumer test links the packaged implementation and checks an EXR
encode/decode round trip without defining `TINYEXR_IMPLEMENTATION` itself.
