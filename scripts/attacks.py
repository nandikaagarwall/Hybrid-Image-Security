import cv2
import numpy as np

def apply_noise(image, noise_type="gaussian", severity=0.01):
    """Applies Gaussian or Salt & Pepper noise."""
    noisy = image.copy()
    if noise_type == "gaussian":
        row, col, ch = noisy.shape
        mean = 0
        sigma = np.sqrt(severity) * 255
        gauss = np.random.normal(mean, sigma, (row, col, ch)).astype(np.float32)
        noisy = cv2.add(noisy.astype(np.float32), gauss)
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
    elif noise_type == "sp":
        row, col, ch = noisy.shape
        s_vs_p = 0.5
        amount = severity
        # Salt
        num_salt = np.ceil(amount * noisy.size * s_vs_p)
        coords = [np.random.randint(0, i - 1, int(num_salt)) for i in noisy.shape[:2]]
        noisy[tuple(coords)] = 255
        # Pepper
        num_pepper = np.ceil(amount * noisy.size * (1.0 - s_vs_p))
        coords = [np.random.randint(0, i - 1, int(num_pepper)) for i in noisy.shape[:2]]
        noisy[tuple(coords)] = 0
    return noisy

def apply_jpeg(image, quality=70):
    """Applies JPEG compression at a given quality level (1-100)."""
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    result, encoded_img = cv2.imencode('.jpg', image, encode_param)
    decoded_img = cv2.imdecode(encoded_img, 1)
    return decoded_img

def apply_blur(image, kernel_size=3):
    """Applies a mean/median blur."""
    return cv2.blur(image, (kernel_size, kernel_size))

def apply_geometric(image, attack_type="cropping"):
    """Applies geometric attacks like cropping or scaling."""
    h, w, _ = image.shape
    attacked = image.copy()
    
    if attack_type == "cropping":
        # Zero out the center 25% of the image
        h_start, h_end = int(h * 0.375), int(h * 0.625)
        w_start, w_end = int(w * 0.375), int(w * 0.625)
        attacked[h_start:h_end, w_start:w_end] = 0
    elif attack_type == "scaling":
        # Downscale by 50% then upscale back to original
        small = cv2.resize(image, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
        attacked = cv2.resize(small, (w, h), interpolation=cv2.INTER_LINEAR)
    elif attack_type == "rotation":
        # Rotate by 2 degrees
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, 2, 1.0)
        attacked = cv2.warpAffine(image, M, (w, h))
        
    return attacked

if __name__ == "__main__":
    test_img = cv2.imread("data/images/lena_watermarked.png")
    
    # Test running an attack
    jpeg_90 = apply_jpeg(test_img, quality=90)
    cv2.imwrite("data/images/lena_attacked_jpeg90.png", jpeg_90)
    print("[✓] Attack module ready. Test JPEG 90 applied and saved.")