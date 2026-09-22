from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get
import os

required_conan_version = ">=2.1"


class TinyExrConan(ConanFile):
    name = "tinyexr"
    description = "Tiny OpenEXR image loader/saver library (C11 API)"
    license = "BSD-3-Clause", "Apache-2.0", "Unlicense"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/syoyo/tinyexr"
    topics = ("exr", "image")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_libdeflate": [True, False],
        "with_thread": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_libdeflate": True,
        "with_thread": False,
    }
    implements = ["auto_shared_fpic"]
    exports_sources = "CMakeLists.txt"

    def export_sources(self):
        export_conandata_patches(self)

    def configure(self):
        self.settings.rm_safe("compiler.cppstd")
        self.settings.rm_safe("compiler.libcxx")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        self.requires("zstd/1.5.7")
        if self.options.with_libdeflate:
            self.requires("libdeflate/1.25")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["TINYEXR_SOURCE_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["TINYEXR_USE_LIBDEFLATE"] = self.options.with_libdeflate
        tc.variables["TINYEXR_USE_THREADS"] = self.options.with_thread
        tc.generate()
        deps = CMakeDeps(self)
        deps.set_property("zstd", "cmake_target_name", "zstd::zstd")
        deps.set_property("zstd::zstdlib", "cmake_target_name", "zstd::zstdlib")
        if self.options.with_libdeflate:
            deps.set_property("libdeflate", "cmake_target_name", "libdeflate::libdeflate")
            deps.set_property("libdeflate::_libdeflate", "cmake_target_name", "libdeflate::library")
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=self.export_sources_folder)
        cmake.build()

    def package(self):
        for name in ("LICENSE", "NOTICE"):
            copy(self, name, src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        CMake(self).install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tinyexr")
        self.cpp_info.set_property("cmake_target_name", "tinyexr::tinyexr")
        self.cpp_info.libs = ["tinyexr3"]
        if self.settings.os in ("Linux", "FreeBSD"):
            self.cpp_info.system_libs.append("m")
            if self.options.with_thread:
                self.cpp_info.system_libs.append("pthread")
