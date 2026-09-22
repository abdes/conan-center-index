from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.files import copy, download, get
import os

required_conan_version = ">=2.1"


class DxcConan(ConanFile):
    name = "dxc"
    description = "Microsoft DirectX Shader Compiler with DXIL and SPIR-V support"
    license = "MIT", "NCSA", "LicenseRef-Microsoft-DXC"
    homepage = "https://github.com/microsoft/DirectXShaderCompiler"
    url = "https://github.com/conan-io/conan-center-index"
    topics = ("hlsl", "shader", "compiler", "dxil", "spirv")
    package_type = "shared-library"
    settings = "os", "arch"

    @property
    def _archive_folder(self):
        return os.path.join(self.build_folder, "distribution")

    def validate(self):
        supported = {"Windows": ("x86", "x86_64", "armv8"), "Linux": ("x86_64",)}
        if str(self.settings.arch) not in supported.get(str(self.settings.os), ()):
            raise ConanInvalidConfiguration(
                "Official DXC binaries support Windows x86/x86_64/armv8 and Linux x86_64. "
                "On macOS, use the DXC supplied by the LunarG Vulkan SDK.")

    def build(self):
        get(self, **self.conan_data["sources"][self.version][str(self.settings.os)],
            destination=self._archive_folder, strip_root=self.settings.os == "Linux")
        if self.settings.os == "Linux":
            # The official 1.9.2607 archive omits this header included by dxcapi.h.
            download(self, **self.conan_data["support_files"][self.version]["win_adapter"],
                     filename=os.path.join(self._archive_folder, "include", "WinAdapter.h"))

    def package(self):
        for pattern in ("LICENSE*", "LICENCE*"):
            copy(self, pattern, src=self._archive_folder, dst=os.path.join(self.package_folder, "licenses"), keep_path=False)
        if self.settings.os == "Windows":
            arch = {"x86": "x86", "x86_64": "x64", "armv8": "arm64"}[str(self.settings.arch)]
            source_bin = os.path.join(self._archive_folder, "bin", arch)
            for name in ("dxc.exe", "dxv.exe", "dxcompiler.dll", "dxil.dll"):
                copy(self, name, src=source_bin, dst=os.path.join(self.package_folder, "bin"))
            copy(self, "*.lib", src=os.path.join(self._archive_folder, "lib", arch),
                 dst=os.path.join(self.package_folder, "lib"))
            source_include = os.path.join(self._archive_folder, "inc")
        else:
            # The Linux release also contains LLVM build artifacts. Package only the public SDK.
            for name in ("dxc", "dxv"):
                copy(self, name, src=os.path.join(self._archive_folder, "bin"),
                     dst=os.path.join(self.package_folder, "bin"))
            for name in ("libdxcompiler.so*", "libdxil.so*"):
                copy(self, name, src=os.path.join(self._archive_folder, "lib"),
                     dst=os.path.join(self.package_folder, "lib"), keep_path=False)
            source_include = os.path.join(self._archive_folder, "include")
        copy(self, "*", src=source_include, dst=os.path.join(self.package_folder, "include"))

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "dxc")
        self.cpp_info.set_property("cmake_target_name", "dxc::dxcompiler")
        self.cpp_info.libs = ["dxcompiler"]
