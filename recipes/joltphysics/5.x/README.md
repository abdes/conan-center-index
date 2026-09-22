# Jolt 5.6 dependencies and compute backends

This recipe supports Jolt 5.6.0 and the older 5.x versions listed in
`../config.yml`. The compute options below exist only for 5.6.0 and later.

## Options and dependencies

Applicable compute options default to enabled. Platform-inapplicable options
are removed. Disabling a backend removes dependencies used only by it.

| Option | Target platforms | Added host/runtime dependencies | Added build tools |
| --- | --- | --- | --- |
| `with_cpu_compute` | Platforms supported by Jolt's CPU backend | None | None |
| `with_dx12` | Windows | `dxc/1.9.2607`, runtime only; DirectX system libraries | DXC |
| `with_vulkan` | Platforms supported by Jolt's Vulkan backend | `vulkan-headers/1.4.357.0`; target-system Vulkan driver | DXC |
| `with_metal` | Apple platforms | Foundation, Metal, and MetalKit frameworks | DXC, `spirv-cross/1.4.357.0`, Xcode Metal tools |

All configurations use `cmake/[>=3.20 <4]` to build Jolt. Windows builds require
the normal compiler and Windows SDK toolchain. Apple builds require the target
Apple SDK. The recipe exposes the required system link libraries/frameworks
and public backend definitions through `Jolt::Jolt`.

**CPU-only builds have no DXC, Vulkan headers, or SPIRV-Cross dependency.**
For example, on Windows:

```text
conan create recipes/joltphysics/5.x --version=5.6.0 --build=missing -o "joltphysics/*:with_dx12=False" -o "joltphysics/*:with_vulkan=False"
```

On Linux only `with_vulkan` needs disabling. On macOS with LunarG installed,
disable both `with_vulkan` and `with_metal` for CPU-only builds. Disable
`with_cpu_compute` as well if no compute backend is wanted; the ordinary
rigid-body physics library remains available.

## DXC on Windows and Linux build machines

For the first GPU build from this fork, export the local DXC recipe with
`conan export recipes/dxc/binary --version=1.9.2607` and use `--build=missing`
when creating/installing Jolt. CPU-only builds do not need this step.

Enabling any GPU backend adds `dxc/1.9.2607` as a build-context tool requirement.
The recipe passes the exact compiler package path to CMake; no system DXC
installation or manual compiler-path configuration is needed. The
[DXC recipe](../../dxc/README.md) describes supported build architectures,
package contents, and its DXIL/SPIR-V tests.

Only DirectX 12 also adds DXC as a host-context runtime requirement, with
headers and link-library traits disabled. Jolt loads `dxcompiler.dll` for
shader reflection at runtime. Vulkan and Metal need DXC only while building
shader assets. Host and build contexts select their respective architectures
when cross-compiling.

The Windows SDK's own `dxc.exe` is not selected: some SDK versions list SPIR-V
options but cannot execute SPIR-V code generation.

## macOS build machines

Microsoft's release does not provide a macOS binary. The small supported
integration path is DXC supplied by the LunarG Vulkan SDK. Discovery checks:

1. An explicit `user.joltphysics:dxc` Conan configuration value.
2. `$VULKAN_SDK/bin/dxc`.
3. `dxc` on `PATH`, for SDK environments that already expose it.

For example:

```text
-c user.joltphysics:dxc=/Users/me/VulkanSDK/<sdk-version>/macOS/bin/dxc
```

If no compiler is found, `config_options()` removes all DXC-requiring GPU
options and reports that they are disabled. CPU compute remains available and
no DXC, Vulkan-header, or SPIRV-Cross dependency is added. The removed GPU
options are absent from the resulting package configuration. To enable them,
install/expose the SDK compiler and resolve the dependency graph again.

If a compiler is found, the GPU options remain available. Metal builds also
require Xcode's `xcrun` and Metal compiler; SPIRV-Cross comes from Conan. The
SDK/compiler must support Jolt's HLSL and SPIR-V flags. Compilation failures
remain errors; a requested backend is not discarded after configuration.

This path uses the installed SDK and is not pinned to Microsoft's binary
release. Pin the LunarG SDK in the build environment when reproducibility is
required. The recipe does not download an SDK, substitute another HLSL
compiler, or build LLVM/DXC from source.

LunarG documentation: <https://vulkan.lunarg.com/doc/view/1.3.283.0/mac/DXC.html>

## Deployment

Compiled `.dxil`, `.spv`, and `Jolt.metallib` assets are installed under
`res/Jolt/Shaders`, exposed through `cpp_info.resdirs`. Applications must deploy
these assets and configure Jolt's shader loader to read them.

For DirectX 12, also deploy the host-context DXC package's runtime DLLs and
notices. `VirtualRunEnv` exposes them during development/tests; the application's
deployer must collect runtime dependencies for distribution. The files belong
to the DXC package and are not duplicated inside the Jolt package.

Jolt loads the Vulkan driver dynamically. The driver is a target-system
prerequisite, not a Conan build-tool dependency.

## Validation boundaries

The consumer test links enabled CPU/DirectX/Vulkan backend classes, checks
packaged shaders, and verifies that the DirectX configuration can load the DXC
runtime and find `DxcCreateInstance`. An Objective-C++ consumer is included for
Metal. These checks do not initialize GPU hardware or validate simulation
behavior.
