#include <tinyexr.h>

#include <cstdio>
#include <cstdlib>

int main() {
    const float pixels[] = {1.0f, 0.5f, 0.25f, 1.0f, 0.0f, 1.0f, 0.5f, 1.0f};
    const char* error = nullptr;
    if (SaveEXR(pixels, 2, 1, 4, 0, "roundtrip.exr", &error) != TINYEXR_SUCCESS) {
        if (error) FreeEXRErrorMessage(error);
        return 1;
    }
    float* decoded = nullptr;
    int width = 0, height = 0;
    const int result = LoadEXR(&decoded, &width, &height, "roundtrip.exr", &error);
    std::remove("roundtrip.exr");
    if (result != TINYEXR_SUCCESS) {
        if (error) FreeEXRErrorMessage(error);
        return 2;
    }
    bool equal = width == 2 && height == 1;
    for (int i = 0; equal && i < 8; ++i) equal = decoded[i] == pixels[i];
    std::free(decoded);
    return equal ? 0 : 3;
}
