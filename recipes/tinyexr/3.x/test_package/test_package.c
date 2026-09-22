#include <exr.h>

#include <stdlib.h>
#include <string.h>

static int roundtrip(exr_compression compression) {
    float pixels[64];
    for (int i = 0; i < 64; ++i) pixels[i] = (float)(i % 8) * 0.25f;
    exr_channel channel = {0};
    strcpy(channel.name, "Y");
    channel.pixel_type = EXR_PIXEL_FLOAT;
    channel.x_sampling = channel.y_sampling = 1;
    void* planes[] = {pixels};
    exr_part part = {0};
    part.width = part.height = 8;
    part.header.part_type = EXR_PART_SCANLINE;
    part.header.data_window.max_x = part.header.data_window.max_y = 7;
    part.header.display_window = part.header.data_window;
    part.header.pixel_aspect_ratio = part.header.screen_window_width = 1.0f;
    part.header.num_channels = 1;
    part.header.channels = &channel;
    part.images = planes;
    exr_image input = {0};
    input.num_parts = 1;
    input.parts = &part;
    void* encoded = NULL;
    size_t size = 0;
    if (exr_save_to_memory(&encoded, &size, NULL, &input, compression) != EXR_SUCCESS) return 1;
    exr_image output = {0};
    exr_result result = exr_load_from_memory(encoded, size, NULL, &output);
    free(encoded);
    if (result != EXR_SUCCESS) return 2;
    int equal = output.num_parts == 1 && output.parts[0].width == 8 && output.parts[0].height == 8
        && output.parts[0].header.num_channels == 1
        && memcmp(output.parts[0].images[0], pixels, sizeof(pixels)) == 0;
    exr_image_free(&output);
    return equal ? 0 : 3;
}

int main(void) {
    exr_set_num_threads(2);
    const exr_compression codecs[] = {
        EXR_COMPRESSION_ZIP, EXR_COMPRESSION_PIZ, EXR_COMPRESSION_ZSTD, EXR_COMPRESSION_HTJ2K256
    };
    for (size_t i = 0; i < sizeof(codecs) / sizeof(codecs[0]); ++i) {
        int result = roundtrip(codecs[i]);
        if (result) return result;
    }
    return 0;
}
