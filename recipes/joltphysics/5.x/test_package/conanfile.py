from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.scm import Version
from pathlib import Path
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "VirtualRunEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["JOLT_TEST_METAL"] = bool(self.dependencies["joltphysics"].options.get_safe("with_metal", False))
        tc.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        dependency = self.dependencies["joltphysics"]
        if Version(dependency.ref.version) >= "5.6.0":
            shader_dir = Path(dependency.package_folder) / "res" / "Jolt" / "Shaders"
            for option, extension in (("with_dx12", "dxil"), ("with_vulkan", "spv"), ("with_metal", "metallib")):
                if dependency.options.get_safe(option):
                    shaders = list(shader_dir.glob(f"*.{extension}"))
                    if not shaders or any(shader.stat().st_size == 0 for shader in shaders):
                        raise RuntimeError(f"Missing packaged {option} shaders")
        if can_run(self):
            bin_path = os.path.join(self.cpp.build.bindirs[0], "test_package")
            self.run(bin_path, env="conanrun")
            if dependency.options.get_safe("with_metal"):
                self.run(os.path.join(self.cpp.build.bindirs[0], "test_metal"), env="conanrun")
