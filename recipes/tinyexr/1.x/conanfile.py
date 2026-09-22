from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get
import os

required_conan_version = ">=2.1"


class TinyExrConan(ConanFile):
    name = "tinyexr"
    description = "Tiny OpenEXR image loader/saver library"
    license = "BSD-3-Clause"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/syoyo/tinyexr"
    topics = ("exr", "image")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_z": ["zlib", "miniz"],
        "with_piz": [True, False],
        "with_zfp": [True, False],
        "with_thread": [True, False],
        "with_openmp": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_z": "miniz",
        "with_piz": True,
        "with_zfp": False,
        "with_thread": False,
        "with_openmp": False,
    }
    implements = ["auto_shared_fpic"]
    exports_sources = "CMakeLists.txt", "tinyexr.cpp"

    def layout(self):
        cmake_layout(self, src_folder="src")

    def requirements(self):
        if self.options.with_z == "miniz":
            self.requires("miniz/3.0.2")
        else:
            self.requires("zlib/[>=1.2.11 <2]")
        if self.options.with_zfp:
            self.requires("zfp/1.0.0")

    def validate(self):
        check_min_cppstd(self, 11)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["TINYEXR_SOURCE_DIR"] = self.source_folder.replace("\\", "/")
        tc.variables["TINYEXR_USE_MINIZ"] = self.options.with_z == "miniz"
        for option in ("piz", "zfp", "thread", "openmp"):
            tc.variables[f"TINYEXR_USE_{option.upper()}"] = self.options.get_safe(f"with_{option}")
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=self.export_sources_folder)
        cmake.build()

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        CMake(self).install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "tinyexr")
        self.cpp_info.set_property("cmake_target_name", "tinyexr::tinyexr")
        self.cpp_info.libs = ["tinyexr"]
        self.cpp_info.defines = [f"TINYEXR_USE_MINIZ={int(self.options.with_z == 'miniz')}"]
        for option in ("piz", "zfp", "thread", "openmp"):
            self.cpp_info.defines.append(f"TINYEXR_USE_{option.upper()}={int(bool(self.options.get_safe(f'with_{option}')))}")
        if self.settings.os in ("Linux", "FreeBSD") and self.options.with_thread:
            self.cpp_info.system_libs.append("pthread")
        if self.options.with_openmp:
            self.cpp_info.set_property("cmake_build_modules", [os.path.join("lib", "cmake", "tinyexr-openmp.cmake")])
