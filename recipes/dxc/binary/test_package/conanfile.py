from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, cmake_layout
from pathlib import Path
import os


class TestPackageConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeDeps", "CMakeToolchain", "VirtualBuildEnv", "VirtualRunEnv"
    test_type = "explicit"

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        self.requires(self.tested_reference_str)

    def build_requirements(self):
        self.tool_requires(self.tested_reference_str)

    def build(self):
        compiler = Path(self.dependencies.build["dxc"].package_folder) / "bin" / (
            "dxc.exe" if self.settings_build.os == "Windows" else "dxc")
        shader = Path(self.source_folder) / "shader.hlsl"
        for filename, flags, magic in (("shader.dxil", "", b"DXBC"),
                                       ("shader.spv", "-spirv", b"\x03\x02\x23\x07")):
            self.run(f'"{compiler}" -T cs_6_0 -E main {flags} "{shader}" -Fo "{filename}"', env="conanbuild")
            if Path(filename).read_bytes()[:4] != magic:
                raise RuntimeError(f"DXC did not produce a valid {filename}")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if can_run(self):
            self.run(os.path.join(self.cpp.build.bindirs[0], "test_package"), env="conanrun")
