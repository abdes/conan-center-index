cmake_minimum_required(VERSION 3.15)
project(tinyexr VERSION 3.2.0 LANGUAGES C)

set(sources
    exr_attr.c exr_b44.c exr_codec.c exr_color.c exr_convert.c exr_core.c
    exr_cpu.c exr_deep.c exr_deflate.c exr_fpnge.c exr_freestanding.c
    exr_gpu_cuda.c exr_half.c exr_jph.c exr_jph_simd.c exr_jph_simd_neon.c
    exr_libdeflate.c exr_mip.c exr_piz.c exr_pxr24.c exr_reader.c exr_resize.c
    exr_rle.c exr_simd_neon.c exr_simd_x86.c exr_spectral.c exr_stdio.c
    exr_thread.c exr_tonemap.c exr_util_simd_neon.c exr_util_simd_x86.c
    exr_vk_vulkan.c exr_writer.c exr_zip.c exr_zstd.c
)
list(TRANSFORM sources PREPEND "${TINYEXR_SOURCE_DIR}/src/")
add_library(tinyexr3 ${sources})
target_compile_features(tinyexr3 PRIVATE c_std_11)
set_target_properties(tinyexr3 PROPERTIES C_EXTENSIONS OFF WINDOWS_EXPORT_ALL_SYMBOLS ON)
if(CMAKE_C_COMPILER_ID STREQUAL "MSVC")
    target_compile_options(tinyexr3 PRIVATE /experimental:c11atomics)
endif()
target_include_directories(tinyexr3 PRIVATE "${TINYEXR_SOURCE_DIR}/include" "${TINYEXR_SOURCE_DIR}/src")

find_package(zstd CONFIG REQUIRED)
target_link_libraries(tinyexr3 PRIVATE zstd::zstd)
if(TINYEXR_USE_LIBDEFLATE)
    find_package(libdeflate CONFIG REQUIRED)
    target_link_libraries(tinyexr3 PRIVATE libdeflate::libdeflate)
    target_compile_definitions(tinyexr3 PRIVATE EXR_USE_LIBDEFLATE EXR_ZLIB_DEFAULT_LIBDEFLATE=1)
endif()
if(TINYEXR_USE_THREADS)
    find_package(Threads REQUIRED)
    target_link_libraries(tinyexr3 PRIVATE Threads::Threads)
    target_compile_definitions(tinyexr3 PRIVATE EXR_USE_THREADS)
endif()
if(UNIX AND NOT APPLE)
    target_link_libraries(tinyexr3 PRIVATE m)
endif()

install(TARGETS tinyexr3 RUNTIME DESTINATION bin LIBRARY DESTINATION lib ARCHIVE DESTINATION lib)
install(DIRECTORY "${TINYEXR_SOURCE_DIR}/include/" DESTINATION include FILES_MATCHING PATTERN "*.h")
