from PIL import Image
import numpy as np
import sys
import os
def psnr(original, stego):
    # Calculate the Mean Squared Error (MSE) between the original and stego images
    mse = np.mean((original - stego) ** 2)

    # If MSE is 0, return infinity to avoid division by zero
    if mse == 0:
        return float('inf')

    # Maximum pixel value in the image
    max_pixel_value = 255.0

    # Calculate and return the Peak Signal-to-Noise Ratio (PSNR)
    return 20 * np.log10(max_pixel_value / np.sqrt(mse))

def embed_LSB(original, message, lsb_count):
    # Get the height and width of the image
    height, width = original.shape

    # Flatten the image array for easier manipulation
    flattened = original.flatten()

    # Convert the message string to binary representation
    message_bits = np.unpackbits(np.array(list(message.encode('utf-8')), dtype=np.uint8))

    # Pad the message bits to match the length of the flattened image
    message_bits = np.pad(message_bits, (0, (len(flattened) - len(message_bits))), 'constant')

    # Embed the message bits in the least significant bits of the image pixels
    for i in range(len(flattened)):
        flattened[i] = (flattened[i] & ~(2 ** lsb_count - 1)) | message_bits[i]

    # Reshape the flattened array back to the original image shape
    stego = flattened.reshape((height, width))
    return stego

def extract_LSB(stego, lsb_count):
    # Flatten the stego image array for easier manipulation
    flattened = stego.flatten()

    # Extract the least significant bits from each pixel
    extracted_bits = [i & (2 ** lsb_count - 1) for i in flattened]

    # Pack the extracted bits into bytes and convert to a string
    extracted_bytes = np.packbits(extracted_bits)
    message = extracted_bytes.tobytes().decode('utf-8').rstrip('\x00')
    return message

def embed_LSB_RGB(original, message, lsb_count):
    # Get the height, width, and number of color channels of the image
    height, width, channels = original.shape

    # Reshape the image to a 2D array where each row represents a pixel and each column represents a color channel
    flattened = original.reshape((-1, channels))

    # Convert the message string to binary representation
    message_bits = np.unpackbits(np.array(list(message.encode('utf-8')), dtype=np.uint8))

    # Pad the message bits to match the length of the flattened image times the number of color channels and LSB count
    message_bits = np.pad(message_bits, (0, (len(flattened) * lsb_count * channels - len(message_bits))), 'constant')

    # Embed the message bits in the least significant bits of each color channel of each pixel
    for i in range(len(flattened)):
        for c in range(channels):
            flattened[i, c] = (flattened[i, c] & ~(2 ** lsb_count - 1)) | message_bits[i * channels + c]

    # Reshape the flattened array back to the original image shape
    stego = flattened.reshape((height, width, channels))
    return stego

def extract_LSB_RGB(stego, lsb_count):
    # Get the height, width, and number of color channels of the stego image
    height, width, channels = stego.shape

    # Reshape the stego image to a 2D array where each row represents a pixel and each column represents a color channel
    flattened = stego.reshape((-1, channels))

    # Extract the least significant bits from each color channel of each pixel
    extracted_bits = []
    for i in range(len(flattened)):
        for c in range(channels):
            extracted_bits.append(flattened[i, c] & (2 ** lsb_count - 1))

    # Pack the extracted bits into bytes and convert to a string
    extracted_bytes = np.packbits(extracted_bits)
    message = extracted_bytes.tobytes().decode('utf-8').rstrip('\x00')
    return message

def main():
    if len(sys.argv) == 6 and sys.argv[1] == "embed":
        original_image_path = sys.argv[2]
        output_image_path = sys.argv[3]
        message = sys.argv[4]
        lsb_count = int(sys.argv[5])
        original_image = Image.open(original_image_path)
        
        num_channels = len(original_image.getbands())
        if num_channels == 1:
            original_image = np.array(original_image.convert('L'))
            stego_image = embed_LSB(original_image, message, lsb_count)
            print("Embedding complete.")
        elif num_channels == 3:
            original_image = np.array(original_image)
            stego_image = embed_LSB_RGB(original_image, message, lsb_count)
            print("Embedding complete.")
        
        psnr_value = psnr(original_image, stego_image)
        print(f"PSNR: {psnr_value:.2f} dB")
        stego_image = Image.fromarray(stego_image.astype(np.uint8))
        stego_image.save(output_image_path)

    elif len(sys.argv) == 4 and sys.argv[1] == "extract":
        stego_image_path = sys.argv[2]
        lsb_count = int(sys.argv[3])

        stego_image = Image.open(stego_image_path)
        
        num_channels = len(stego_image.getbands())
        if num_channels == 1:
            stego_image = np.array(stego_image.convert('L'))
            extracted_msg = extract_LSB(stego_image, lsb_count)
        elif num_channels == 3:
            stego_image = np.array(stego_image)
            extracted_msg = extract_LSB_RGB(stego_image, lsb_count)

        print(f"Extracted Message: {extracted_msg}")
    else:
        print("Usage for embedding: python LSB.py embed <original_image.bmp> <output_image.bmp> <message> <lsb_count>")
        print("Usage for extracting: python LSB.py extract <stego_image.bmp> <lsb_count>")
        sys.exit(1)

if __name__ == "__main__":
    main()
