"""Values reported in Sanivarapu et al., Appl. Sci. 12:8724 (2022), Tables 2-4 (12 images each)."""
import numpy as np
PSNR_NO_ATTACK = [42.25, 43.56, 42.85, 43.12, 42.22, 41.81, 41.68, 40.35, 41.74, 43.36, 43.81, 42.65]
NCC = {  # attack in our naming : (their 12 per-image NCC values, their stated parameter)
    "Salt&Pepper d=0.01": ([.9789, .9796, .9898, .9899, .9887, .9815, .9829, .9867, .9814, .9885, .9829, .9785], "density 0.5 (as stated)"),
    "Gaussian v=0.01":   ([.9898, .9885, .9896, .9901, .9914, .9912, .9908, .9925, .9904, .9916, .9892, .9845], "variance 0.01"),
    "Avg blur 3x3":      ([.9901, .9905, .9908, .9906, .9910, .9903, .9907, .9915, .9911, .9916, .9914, .9909], "mean filter 3x3"),
    "JPEG Q=90":         ([.9938, .9942, .9935, .9932, .9949, .9936, .9937, .9932, .9941, .9934, .9914, .9909], "Q = 90"),
    "Centre blank 6.25%": ([.9801, .9815, .9836, .9885, .9869, .9878, .9886, .9891, .9912, .9905, .9897, .9856], "cropping, size not stated"),
    "Rotation 2 deg":    ([.9896, .9889, .9885, .9889, .9904, .9911, .9919, .9921, .9902, .9919, .9901, .9842], "angle not stated"),
    "Scaling 0.5x->1x":  ([.9964, .9948, .9947, .9957, .9954, .9958, .9961, .9955, .9961, .9951, .9968, .9964], "down-sampled twice"),
    "Translation 2 px":  ([.9777, .9765, .9787, .9789, .9778, .9781, .9776, .9785, .9788, .9781, .9782, .9778], "2 px in x and y"),
}
MEAN_NCC = {k: float(np.mean(v[0])) for k, v in NCC.items()}

# PSNR of the attacked watermarked image, Tables 3-4 of the base paper (same image order as PSNR_NO_ATTACK:
# House, Tree, Girl, Mandrill, Lena, Jetplane, Lake, Pepper, House 2, Einstein, Monalisa, Monarch).
# Keys use our attack names; the base paper's own attack settings are in NCC[...][1].
PSNR_ATTACKED = {
    'Salt&Pepper d=0.01': [36.11, 36.05, 35.56, 35.66, 35.28, 35.47, 35.22, 35.84, 36.24, 36.05, 35.69, 35.88],
    'Gaussian v=0.01': [39.01, 38.87, 38.86, 38.96, 38.15, 38.42, 38.36, 38.51, 39.12, 39.21, 39.11, 39.05],
    'Avg blur 3x3': [33.12, 33.25, 33.18, 33.22, 33.15, 33.16, 33.11, 33.08, 33.13, 33.17, 33.22, 33.2],
    'JPEG Q=90': [37.12, 37.28, 37.25, 37.24, 37.16, 37.21, 37.27, 37.28, 37.24, 37.28, 37.22, 37.24],
    'Centre blank 6.25%': [28.36, 29.05, 29.23, 29.26, 28.21, 29.6, 29.35, 29.48, 29.54, 29.22, 29.35, 29.32],
    'Rotation 2 deg': [29.06, 28.58, 29.12, 29.14, 28.12, 27.86, 28.26, 27.87, 28.56, 29.14, 29.04, 28.87],
    'Scaling 0.5x->1x': [38.66, 38.59, 39.28, 39.22, 38.92, 37.99, 38.84, 37.94, 38.65, 39.19, 39.21, 38.92],
    'Translation 2 px': [36.42, 36.28, 36.19, 36.33, 36.23, 36.19, 36.28, 36.22, 36.18, 36.19, 36.24, 36.28],
}
MEAN_PSNR_ATTACKED = {k: float(np.mean(v)) for k, v in PSNR_ATTACKED.items()}
