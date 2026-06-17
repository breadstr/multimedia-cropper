#include <stdio.h>
#include <stdlib.h>

typedef struct  {
    unsigned char b;
    unsigned char g;
    unsigned char r;
} Pixel;


int checkImage(Pixel **pixels, int img_height, int img_width);

Pixel** createImage(int img_height, int img_width);

Pixel** loadImage(Pixel** empty_image, int img_height, int img_width, FILE *file);

Pixel** cropImage(Pixel** original_image, int new_width, int img_height, int img_width);

void writeCroppedBMP(const char* filename, Pixel** pixels, int new_dim, unsigned char* old_header);


int main(int argc, char *argv[]) {
    if (argc < 2) {
        printf("Usage: cropper <filename.bmp>\n");
        return 1;
    }
    
    char *filename = argv[1]; // Use the name passed from Python
    FILE *file = fopen(filename, "rb");

    if (!file) {
        printf("Could not open file.\n");
        return 1;
    }

    unsigned char header[54];
    fread(header, sizeof(unsigned char), 54, file);
    int width = *(int*)&header[18];
    int height = *(int*)&header[22];

    Pixel** pixels = createImage(height, width);
    loadImage(pixels, height, width, file); 
    fclose(file);

    if (checkImage(pixels, height, width)) {
            printf("Black bars detected. Proceeding to crop...\n");
            
            Pixel** new_img = cropImage(pixels, height, height, width);
            if (new_img) {
                writeCroppedBMP(filename, new_img, height, header); 

                
                // Clean up the cropped image memory
                for (int i = 0; i < height; i++) free(new_img[i]);
                    free(new_img);
            }
} 
    else {
            printf("Image is already square or not padded.\n");
        }

    // Clean up the original image memory
    for (int i = 0; i < height; i++) free(pixels[i]);
    free(pixels);

    return 0;
}

int checkImage(Pixel **pixels, int img_height, int img_width) {

    int bar_width = (img_width-img_height)/2;
    int match_count = 0;

    for (int y = 0; y < img_height; y += 10) {
        Pixel left_bar = pixels[y][bar_width/2];
        Pixel right_bar = pixels[y][img_width - 1 - (bar_width / 2)];
        
        if (abs(left_bar.r - right_bar.r) < 10 && 
            abs(left_bar.g - right_bar.g) < 10 && 
            abs(left_bar.b - right_bar.b) < 10) {
                match_count += 1;
        }

    }
    
    return (match_count > (img_height / 10) * 0.9);
}

Pixel** createImage(int img_height, int img_width) {
    //frees memory with specified height and width
    Pixel **pixels;

    pixels = (Pixel **)malloc(img_height * sizeof(*pixels));    
    if (pixels == NULL) 
        return NULL;

    for (int i = 0; i < img_height; i++) {
        pixels[i] = (Pixel *)malloc(img_width * sizeof(Pixel));
        if (pixels[i] == NULL) {
            // raise execption C assert
            for (int j = 0; j < i; j++) 
                free(pixels[j]);
            free(pixels);
            return NULL;
        }
    }

    return pixels;
}

Pixel** loadImage(Pixel** pixels, int img_height, int img_width, FILE* file) {
    fseek(file, 54, SEEK_SET);

    int padding = (4 - (img_width * 3) % 4) % 4;

    for (int i = 0; i < img_height; i++) {
        fread(pixels[i], sizeof(Pixel), img_width, file);
        fseek(file, padding, SEEK_CUR);
    }
    return pixels;
}

Pixel** cropImage(Pixel** original_image, int new_width, int img_height, int img_width) {

    int off_set = (img_width - img_height) / 2;
    Pixel** cropped_img = createImage(img_height, img_height);
    
    if (cropped_img == NULL) {
        return NULL;
    }

    for (int y = 0; y < img_height; y++) {
        for (int x = 0; x < img_height; x++) {
        // We stay on the same row (y), 
        // but we jump ahead by 280 pixels (offset_x) in the original
            cropped_img[y][x] = original_image[y][x + off_set];
        }
    }   

    return cropped_img;
}

void writeCroppedBMP(const char* filename, Pixel** pixels, int new_dim, unsigned char* old_header) {
    
    // Calculate BMP row padding to align byte arrays to a multiple of 4
    int padding = (4 - (new_dim * 3) % 4) % 4;
    FILE* out = fopen(filename, "wb"); 
    if (!out) return;

    unsigned char new_header[54];
    for(int i = 0; i < 54; i++) {
        new_header[i] = old_header[i];
}

    // Update specific raw binary offset fields for width, height, and file sizes
    *(int*)&new_header[18] = new_dim;
    *(int*)&new_header[22] = new_dim;
    *(int*)&new_header[34] = new_dim * new_dim * 3;
    // Total file size = 54 (header) + (width * height * 3) + (padding * height)
    int new_total_size = 54 + (new_dim * new_dim * 3) + (padding * new_dim);
    *(int*)&new_header[2] = new_total_size;

    //write the header
    fwrite(new_header, 1, 54, out);

    // Insert null padding bytes to fulfill file specification requirements
    for (int i = 0; i < new_dim; i++) {
        fwrite(pixels[i], sizeof(Pixel), new_dim, out);
        
        for (int p = 0; p < padding; p++) {
            fputc(0, out);
        }
    }

    fclose(out);
}