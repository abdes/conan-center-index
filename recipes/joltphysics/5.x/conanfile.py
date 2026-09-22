from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.apple import is_apple_os
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import copy, get, rmdir, rm, export_conandata_patches, apply_conandata_patches
from conan.tools.microsoft import is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os
import shutil

required_conan_version = ">=2.0.9"


class JoltPhysicsConan(ConanFile):
    name = "joltphysics"
    description = (
        "A multi core friendly rigid body physics and collision detection "
        "library, written in C++, suitable for games and VR applications."
    )
    license = "MIT"
    topics = ("physics", "simulation", "physics-engine", "physics-simulation", "rigid-body", "game", "collision")
    homepage = "https://github.com/jrouwe/JoltPhysics"
    url = "https://github.com/conan-io/conan-center-index"

    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_cpu_compute": [True, False],
        "with_dx12": [True, False],
        "with_vulkan": [True, False],
        "with_metal": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_cpu_compute": True,
        "with_dx12": True,
        "with_vulkan": True,
        "with_metal": True,
    }
    implements = ["auto_shared_fpic"]

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")
        if Version(self.version) < "5.6.0":
            for option in ("with_cpu_compute", "with_dx12", "with_vulkan", "with_metal"):
                self.options.rm_safe(option)
        else:
            if self.settings.os != "Windows":
                self.options.rm_safe("with_dx12")
            if not is_apple_os(self):
                self.options.rm_safe("with_metal")
            if self.settings_build.os == "Macos" and not self._macos_dxc:
                for option in ("with_dx12", "with_vulkan", "with_metal"):
                    self.options.rm_safe(option)
                self.output.info("LunarG DXC not found on macOS; GPU compute options are disabled.")

    @property
    def _macos_dxc(self):
        sdk = os.environ.get("VULKAN_SDK")
        candidates = (
            self.conf.get("user.joltphysics:dxc", check_type=str),
            os.path.join(sdk, "bin", "dxc") if sdk else None,
            shutil.which("dxc"),
        )
        return next((os.path.abspath(path) for path in candidates
                     if path and os.path.isfile(path) and os.access(path, os.X_OK)), None)

    @property
    def _with_gpu(self):
        return any(self.options.get_safe(option, False) for option in ("with_dx12", "with_vulkan", "with_metal"))

    @property
    def _jolt_build_type(self):
        if self.settings.build_type == "RelWithDebInfo":
            return "Release"
        return str(self.settings.build_type)

    def export_sources(self):
        export_conandata_patches(self)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def build_requirements(self):
        self.tool_requires("cmake/[>=3.20 <4]")
        if self._with_gpu and self.settings_build.os != "Macos":
            self.tool_requires("dxc/1.9.2607")
        if self.options.get_safe("with_metal"):
            self.tool_requires("spirv-cross/1.4.357.0")

    def requirements(self):
        if self.options.get_safe("with_dx12"):
            # Jolt loads the host DXC library for runtime shader reflection.
            self.requires("dxc/1.9.2607", headers=False, libs=False, run=True)
        if self.options.get_safe("with_vulkan"):
            self.requires("vulkan-headers/1.4.357.0", transitive_headers=True)

    def validate(self):
        check_min_cppstd(self, 17)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        if Version(self.version) >= "5.6.0":
            for option, switch in (("with_cpu_compute", "CPU_COMPUTE"), ("with_dx12", "DX12"),
                                   ("with_vulkan", "VK"), ("with_metal", "MTL")):
                tc.cache_variables[f"JPH_USE_{switch}"] = bool(self.options.get_safe(option, False))
            tc.cache_variables["JPH_BUILD_SHARED_LIBS"] = self.options.shared
            if self._with_gpu:
                if self.settings_build.os == "Macos":
                    # Microsoft does not publish macOS binaries. LunarG's SDK supplies DXC.
                    dxc = self._macos_dxc
                    if not dxc:
                        raise ConanInvalidConfiguration(
                            "LunarG DXC disappeared after the GPU compute options were configured.")
                else:
                    compiler = "dxc.exe" if self.settings_build.os == "Windows" else "dxc"
                    dxc = os.path.join(self.dependencies.build["dxc"].package_folder, "bin", compiler)
                tc.cache_variables["DXC_COMPILER"] = os.path.abspath(dxc).replace("\\", "/")
            if self.options.get_safe("with_metal"):
                spirv_cross = self.dependencies.build["spirv-cross"]
                tc.cache_variables["SPIRV_CROSS_COMPILER"] = os.path.join(
                    spirv_cross.package_folder, "bin", "spirv-cross").replace("\\", "/")
        tc.cache_variables["TARGET_UNIT_TESTS"] = False
        tc.cache_variables["TARGET_HELLO_WORLD"] = False
        tc.cache_variables["TARGET_PERFORMANCE_TEST"] = False
        tc.cache_variables["TARGET_SAMPLES"] = False
        tc.cache_variables["TARGET_VIEWER"] = False
        tc.cache_variables["CROSS_PLATFORM_DETERMINISTIC"] = False
        tc.cache_variables["INTERPROCEDURAL_OPTIMIZATION"] = False
        tc.cache_variables["GENERATE_DEBUG_SYMBOLS"] = self.settings.build_type == "RelWithDebInfo"
        if self.settings.build_type == "RelWithDebInfo":
            tc.cache_variables["CMAKE_CONFIGURATION_TYPES"] = "Release"
        tc.cache_variables["ENABLE_ALL_WARNINGS"] = False
        tc.cache_variables["OVERRIDE_CXX_FLAGS"] = False
        tc.cache_variables["DEBUG_RENDERER_IN_DEBUG_AND_RELEASE"] = False
        tc.cache_variables["PROFILER_IN_DEBUG_AND_RELEASE"] = False
        if is_msvc(self):
            tc.cache_variables["USE_STATIC_MSVC_RUNTIME_LIBRARY"] = is_msvc_static_runtime(self)
        tc.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure(build_script_folder=os.path.join(self.source_folder, "Build"))
        cmake.build(build_type=self._jolt_build_type if cmake.is_multi_configuration else None)

    def package(self):
        copy(self, "LICENSE", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install(build_type=self._jolt_build_type if cmake.is_multi_configuration else None)
        if self._with_gpu:
            shader_dir = os.path.join(self.package_folder, "share", "Jolt", "Shaders")
            copy(self, "*", src=shader_dir, dst=os.path.join(self.package_folder, "res", "Jolt", "Shaders"))
            rmdir(self, os.path.join(self.package_folder, "share"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rm(self, "*.cmake", os.path.join(self.package_folder, "include", "Jolt"))

    def package_info(self):
        self.cpp_info.libs = ["Jolt"]
        self.cpp_info.set_property("cmake_file_name", "Jolt")
        self.cpp_info.set_property("cmake_target_name", "Jolt::Jolt")
        # INFO: The CMake option ENABLE_OBJECT_STREAM is enabled by default and defines JPH_OBJECT_STREAM as public
        # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Build/CMakeLists.txt#L95C8-L95C28
        self.cpp_info.defines = ["JPH_OBJECT_STREAM"]
        if Version(self.version) >= "5.6.0":
            for option, define in (("with_cpu_compute", "JPH_USE_CPU_COMPUTE"), ("with_dx12", "JPH_USE_DX12"),
                                   ("with_vulkan", "JPH_USE_VK"), ("with_metal", "JPH_USE_MTL")):
                if self.options.get_safe(option):
                    self.cpp_info.defines.append(define)
            if self.options.get_safe("with_dx12"):
                self.cpp_info.system_libs.extend(["dxgi", "d3d12", "d3dcompiler", "dxguid"])
            if self.options.get_safe("with_vulkan") and self.settings.os in ("Linux", "FreeBSD"):
                self.cpp_info.system_libs.append("dl")
            if self.options.get_safe("with_metal"):
                self.cpp_info.frameworks.extend(["Foundation", "Metal", "MetalKit"])
            if self._with_gpu:
                self.cpp_info.resdirs = [os.path.join("res", "Jolt", "Shaders")]
        # INFO: Public defines exposed in include/Jolt/Jolt.cmake
        # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Build/CMakeLists.txt#L51
        if self.settings.arch in ["x86_64", "x86"]:
            self.cpp_info.defines.extend(["JPH_USE_AVX2", "JPH_USE_AVX", "JPH_USE_SSE4_1",
                                          "JPH_USE_SSE4_2", "JPH_USE_LZCNT", "JPH_USE_TZCNT",
                                          "JPH_USE_F16C", "JPH_USE_FMADD"])
        if is_msvc(self):
            # INFO: Floating point exceptions are enabled by default
            # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Build/CMakeLists.txt#L37
            # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Jolt/Jolt.cmake#L529
            self.cpp_info.defines.append("JPH_FLOATING_POINT_EXCEPTIONS_ENABLED")

        if self.options.shared:
            # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Jolt/Jolt.cmake#L495
            self.cpp_info.defines.append("JPH_SHARED_LIBRARY")

        # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Build/CMakeLists.txt#L48
        # https://github.com/jrouwe/JoltPhysics/blob/v5.2.0/Jolt/Jolt.cmake#L554
        self.cpp_info.defines.append("JPH_OBJECT_LAYER_BITS=16")

        if self.settings.os in ["Linux", "FreeBSD"]:
            self.cpp_info.system_libs.append("pthread")
