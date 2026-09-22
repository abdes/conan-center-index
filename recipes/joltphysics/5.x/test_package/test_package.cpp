#include <cstdlib>
#include <Jolt/Jolt.h>
#include <Jolt/Core/Factory.h>
#include <Jolt/RegisterTypes.h>

#ifdef JPH_USE_CPU_COMPUTE
#include <Jolt/Compute/CPU/ComputeSystemCPU.h>
#endif
#ifdef JPH_USE_DX12
#include <Jolt/Compute/DX12/ComputeSystemDX12.h>
#endif
#ifdef JPH_USE_VK
#include <Jolt/Compute/VK/ComputeSystemVKWithAllocator.h>
#endif

int main() {
    JPH::RegisterDefaultAllocator();
    auto factory = JPH::Factory();
#ifdef JPH_USE_CPU_COMPUTE
    JPH::ComputeSystemCPU cpu;
#endif
#ifdef JPH_USE_DX12
    JPH::ComputeSystemDX12 dx12;
    HMODULE compiler = LoadLibraryW(L"dxcompiler.dll");
    if (!compiler) return EXIT_FAILURE;
    const bool has_factory = GetProcAddress(compiler, "DxcCreateInstance") != nullptr;
    FreeLibrary(compiler);
    if (!has_factory) return EXIT_FAILURE;
#endif
#ifdef JPH_USE_VK
    JPH::ComputeSystemVKWithAllocator vulkan;
#endif
    JPH::UnregisterTypes();
    return EXIT_SUCCESS;
}
