from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy, save
from conan.tools.layout import basic_layout
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps
import os

required_conan_version = ">=1.52.0"

class TinyExrConan(ConanFile):
    name = "tinyexr"
    description = "Tiny OpenEXR image loader/saver library"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/syoyo/tinyexr"
    topics = ("exr", "header-only")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "with_z": ["zlib", "miniz"],
        "with_piz": [True, False],
        "with_zfp": [True, False],
        "with_thread": [True, False],
        "with_openmp": [True, False],
        "shared": [True, False],
    }
    default_options = {
        "with_z": "miniz",
        "with_piz": True,
        "with_zfp": False,
        "with_thread": False,
        "with_openmp": False,
        "shared": False,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        basic_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_z == "miniz":
            self.requires("miniz/3.0.2")
        else:
            self.requires("zlib/[>=1.2.11 <2]")
        if self.options.with_zfp:
            self.requires("zfp/1.0.0")

    def validate(self):
        if self.options.with_thread and self.settings.compiler.get_safe("cppstd"):
            check_min_cppstd(self, "11")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        # Detect header-only releases (no tinyexr.cc means header-only)
        self._header_only = not os.path.exists(os.path.join(self.source_folder, "tinyexr.cc"))

    def package_id(self):
        # For header-only releases the package id should be independent of settings
        if getattr(self, "_header_only", False):
            self.info.clear()

    @property
    def _extracted_license(self):
        # Prefer top-level LICENSE file if present
        license_path = os.path.join(self.source_folder, "LICENSE")
        if os.path.isfile(license_path):
            return open(license_path, "r", encoding="utf-8").read()
        # Fallback: extract header comment from tinyexr.h
        header_path = os.path.join(self.source_folder, "tinyexr.h")
        if os.path.isfile(header_path):
            content_lines = open(header_path, "r", encoding="utf-8").readlines()
            # Try to extract a reasonable chunk from the top of the file
            license_content = []
            for i in range(min(0, len(content_lines)) , min(40, len(content_lines))):
                license_content.append(content_lines[i].rstrip('\n'))
            return "\n".join(license_content)
        return ""

    def build(self):
        apply_conandata_patches(self)
        # Skip build for header-only releases
        if getattr(self, "_header_only", False):
            return
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def generate(self):
        # Skip generating CMake toolchain if header-only
        if getattr(self, "_header_only", False):
            return
        tc = CMakeToolchain(self)
        # Propagate options to the upstream CMakeLists
        tc.variables["TINYEXR_USE_MINIZ"] = "ON" if self.options.with_z == "miniz" else "OFF"
        tc.variables["TINYEXR_USE_PIZ"] = "ON" if self.options.with_piz else "OFF"
        tc.variables["TINYEXR_USE_ZFP"] = "ON" if self.options.with_zfp else "OFF"
        tc.variables["TINYEXR_USE_THREAD"] = "ON" if self.options.with_thread else "OFF"
        tc.variables["TINYEXR_USE_OPENMP"] = "ON" if self.options.with_openmp else "OFF"
        # Do not build samples/tests in package build
        tc.variables["TINYEXR_BUILD_SAMPLE"] = "OFF"
        # Respect `shared` option
        tc.variables["BUILD_SHARED_LIBS"] = "ON" if self.options.shared else "OFF"
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def package(self):
        # License
        license_folder = os.path.join(self.package_folder, "licenses")
        os.makedirs(license_folder, exist_ok=True)
        save(self, os.path.join(license_folder, "LICENSE"), self._extracted_license)

        # Headers
        copy(self, pattern="tinyexr.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        # If not header-only, copy built libs/binaries from the build folder
        if not getattr(self, "_header_only", False):
            lib_dst = os.path.join(self.package_folder, "lib")
            os.makedirs(lib_dst, exist_ok=True)
            for root, _dirs, files in os.walk(self.build_folder):
                for fname in files:
                    if fname.endswith(('.lib', '.a', '.so', '.dylib')):
                        copy(self, pattern=fname, src=root, dst=lib_dst)

            # Binaries / shared runtime files (if any)
            bin_dst = os.path.join(self.package_folder, "bin")
            os.makedirs(bin_dst, exist_ok=True)
            for root, _dirs, files in os.walk(self.build_folder):
                for fname in files:
                    if os.name == 'nt' and (fname.endswith('.exe') or fname.endswith('.dll')):
                        copy(self, pattern=fname, src=root, dst=bin_dst)

    def package_info(self):
        # Compile-time defines to match upstream options (always provided)
        self.cpp_info.defines.append("TINYEXR_USE_MINIZ={}".format("1" if self.options.with_z == "miniz" else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_PIZ={}".format("1" if self.options.with_piz else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_ZFP={}".format("1" if self.options.with_zfp else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_THREAD={}".format("1" if self.options.with_thread else "0"))
        self.cpp_info.defines.append("TINYEXR_USE_OPENMP={}".format("1" if self.options.with_openmp else "0"))

        # Header-only: no libs; Built: provide tinyexr lib
        if getattr(self, "_header_only", False):
            self.cpp_info.bindirs = []
            self.cpp_info.libdirs = []
        else:
            self.cpp_info.libs = ["tinyexr"]

        if self.settings.os in ["Linux", "FreeBSD"] and self.options.with_thread:
            self.cpp_info.system_libs.append("pthread")
