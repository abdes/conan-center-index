#ifdef _WIN32
#include <windows.h>
#endif
#include <dxcapi.h>

#include <cstring>
#include <iostream>
#include <memory>

struct ReleaseInterface {
    template <typename T>
    void operator()(T* value) const {
        if (value) value->Release();
    }
};

int main() {
    IDxcCompiler3* raw_compiler = nullptr;
    if (FAILED(DxcCreateInstance(CLSID_DxcCompiler, IID_PPV_ARGS(&raw_compiler)))) return 1;
    std::unique_ptr<IDxcCompiler3, ReleaseInterface> compiler(raw_compiler);

    const char shader[] = "RWStructuredBuffer<uint> output : register(u0); "
        "[numthreads(1, 1, 1)] void main(uint3 id : SV_DispatchThreadID) { output[id.x] = id.x + 1; }";
    DxcBuffer source = {shader, sizeof(shader) - 1, DXC_CP_UTF8};
    for (bool spirv : {false, true}) {
        const wchar_t* arguments[] = {L"-T", L"cs_6_0", L"-E", L"main", L"-spirv"};
        IDxcResult* raw_result = nullptr;
        if (FAILED(compiler->Compile(&source, arguments, spirv ? 5 : 4, nullptr, IID_PPV_ARGS(&raw_result)))) return 2;
        std::unique_ptr<IDxcResult, ReleaseInterface> result(raw_result);
        HRESULT status = E_FAIL;
        if (FAILED(result->GetStatus(&status)) || FAILED(status)) return 3;
        IDxcBlob* raw_object = nullptr;
        if (FAILED(result->GetResult(&raw_object))) return 4;
        std::unique_ptr<IDxcBlob, ReleaseInterface> object(raw_object);
        const char* magic = spirv ? "\x03\x02\x23\x07" : "DXBC";
        if (object->GetBufferSize() < 4 || std::memcmp(object->GetBufferPointer(), magic, 4) != 0) return 5;
    }
    std::cout << "DXC runtime compiled DXIL and SPIR-V successfully\n";
    return 0;
}
