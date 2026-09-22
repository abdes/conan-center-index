# DirectX Shader Compiler (DXC)

`dxc/1.9.2607` packages Microsoft's official July 2026 binary release. It
provides both the HLSL compiler executable and its shared-library API, with
DXIL and SPIR-V code generation enabled.

This recipe is maintained in this fork. Before resolving a consumer against
the local checkout, export the recipe to the Conan cache:

```text
conan export recipes/dxc/binary --version=1.9.2607
```

Use `--build=missing` when creating/installing the consumer. Conan will assemble
the package from the verified release archive. Exporting does not upload it to
a remote or install anything system-wide.

## Supported platforms

| Operating system | Conan architectures | Distribution |
| --- | --- | --- |
| Windows | `x86`, `x86_64`, `armv8` | Architecture-specific files from Microsoft's Windows ZIP |
| Linux | `x86_64` | Microsoft's Linux tarball |
| macOS | Not packaged | Use LunarG Vulkan SDK DXC; see the Jolt recipe's macOS behavior |

Unsupported OS/architecture pairs fail recipe validation. The package ID
depends on OS and architecture, not the consumer's compiler or Debug/Release
configuration, because these are upstream prebuilt binaries. Linux requires a
glibc-based environment compatible with the upstream binaries.

The release archives are pinned by URL and SHA-256 in `binary/conandata.yml`.
The Linux 1.9.2607 archive omits `WinAdapter.h`, which `dxcapi.h` includes. The
recipe downloads that header from the same release tag, verifies its own
SHA-256, and installs it alongside the other public headers. It does not patch
or substitute the compiler binaries.

## Use as a build tool

```python
def build_requirements(self):
    self.tool_requires("dxc/1.9.2607")
```

Conan selects the binary for the build machine. With `VirtualBuildEnv`, its
`bin` directory and runtime-library search paths are available in `conanbuild`.
A recipe can also pass the exact compiler path to CMake:

```python
dxc = self.dependencies.build["dxc"]
executable = "dxc.exe" if self.settings_build.os == "Windows" else "dxc"
tc.cache_variables["DXC_COMPILER"] = os.path.join(dxc.package_folder, "bin", executable)
```

Typical shader compilation commands are:

```text
dxc -T cs_6_0 -E main shader.hlsl -Fo shader.dxil
dxc -T cs_6_0 -E main -spirv shader.hlsl -Fo shader.spv
```

## Use the library or runtime

For code calling the compiler API, add a normal requirement:

```python
def requirements(self):
    self.requires("dxc/1.9.2607")
```

Then consume the generated CMake target:

```cmake
find_package(dxc CONFIG REQUIRED)
target_link_libraries(my_target PRIVATE dxc::dxcompiler)
```

Include `<dxcapi.h>`; on Windows, include `<windows.h>` first. The target
supplies public headers and the `dxcompiler` import/shared library.

If code loads the runtime dynamically and does not need headers or linkage:

```python
self.requires("dxc/1.9.2607", headers=False, libs=False, run=True)
```

A normal requirement selects the application's target architecture, which can
differ from the build machine. A project that compiles shaders during its build
and uses DXC at runtime can require the same version in both contexts, as the
Jolt DirectX 12 backend does.

`VirtualRunEnv` provides runtime search paths during development and tests.
Application deployment must copy the host package's runtime files; a build-only
`tool_requires` is not a deployment dependency.

## Package contents

| Directory | Windows | Linux |
| --- | --- | --- |
| `bin` | `dxc.exe`, `dxv.exe`, `dxcompiler.dll`, `dxil.dll` | `dxc`, `dxv` |
| `lib` | `dxcompiler.lib`, `dxil.lib` | `libdxcompiler.so`, `libdxil.so` |
| `include` | Public DXC/HLSL headers | Public headers plus the missing `WinAdapter.h` |
| `licenses` | Upstream license files | Upstream license files |

The runtime files remain separate from packages that consume DXC. Keep the
upstream license notices when redistributing them. LLVM build intermediates
and unrelated executables included in the Linux release archive are excluded
from the Conan package.

## Validation

Run `conan create recipes/dxc/binary --version=1.9.2607 --build=missing` from the
repository root with suitable build and host profiles.

The consumer test requires DXC in both contexts. It compiles a compute shader
to DXIL and SPIR-V using the build-context executable and checks both output
signatures. It then builds a C++ consumer of `dxc::dxcompiler`. When the host
binary can run, the consumer creates `IDxcCompiler3` and compiles both formats
through the shared-library API. This exercises runtime loading as well as
headers, linkage, and compiler functionality.

Upstream release: <https://github.com/microsoft/DirectXShaderCompiler/releases/tag/v1.9.2607>
