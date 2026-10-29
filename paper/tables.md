## Table 1: Imperceptibility per image

| Image    |   Base paper PSNR (reported) |   A PSNR (dB) |   A SSIM |   A* PSNR (dB) |   A* SSIM |   B PSNR (dB) |   B SSIM |   C PSNR (dB) |   C SSIM |
|:---------|-----------------------------:|--------------:|---------:|---------------:|----------:|--------------:|---------:|--------------:|---------:|
| airplane |                        41.81 |       40.15   |   0.9934 |        38.45   |    0.9909 |        39.12  |   0.9911 |       40.14   |   0.9934 |
| boat     |                        42.65 |       40.13   |   0.9963 |        38.45   |    0.9948 |        36.18  |   0.9909 |       40.12   |   0.9963 |
| einstein |                        43.36 |       40.08   |   0.9968 |        38.4    |    0.9956 |        36.51  |   0.9927 |       40.07   |   0.9968 |
| girl     |                        42.85 |       40.14   |   0.9881 |        38.46   |    0.9836 |        38.4   |   0.9851 |       40.12   |   0.9881 |
| house    |                        42.25 |       40.1    |   0.9917 |        38.42   |    0.9886 |        37.96  |   0.9896 |       40.09   |   0.9917 |
| house2   |                        41.74 |       40.11   |   0.9958 |        38.42   |    0.9942 |        34.74  |   0.9843 |       40.1    |   0.9958 |
| lake     |                        41.68 |       40.07   |   0.9971 |        38.39   |    0.9959 |        34.9   |   0.9886 |       40.06   |   0.9971 |
| lena     |                        42.22 |       40.14   |   0.9953 |        38.44   |    0.9934 |        38.9   |   0.9931 |       40.13   |   0.9953 |
| mandrill |                        43.12 |       40.11   |   0.9984 |        38.44   |    0.9977 |        34.42  |   0.9934 |       40.1    |   0.9984 |
| monalisa |                        43.81 |       40.1    |   0.9865 |        38.42   |    0.9814 |        49.13  |   0.9977 |       40.09   |   0.9865 |
| peppers  |                        40.35 |       40.21   |   0.9944 |        38.52   |    0.9921 |        36.77  |   0.9889 |       40.2    |   0.9944 |
| tree     |                        43.56 |       40.12   |   0.9956 |        38.43   |    0.9939 |        34.83  |   0.9841 |       40.11   |   0.9956 |
| Mean     |                        42.45 |       40.1217 |   0.9941 |        38.4367 |    0.9918 |        37.655 |   0.99   |       40.1108 |   0.9941 |

Base paper reports PSNR only (Table 2 of Sanivarapu et al.); its 'Monarch' and 'Jetplane' are taken as our 'boat' and 'airplane'. C carries 0.10 bpp of encrypted payload.

## Table 2: Robustness under attacks

| Attack             |   A NCC |   A BER % | A QR ok   |   A* NCC |   A* BER % | A* QR ok   |   B NCC |   B BER % | B QR ok   |   C NCC |   C BER % | C QR ok   |   C payload BER | C message ok   |   Base paper NCC (reported) |
|:-------------------|--------:|----------:|:----------|---------:|-----------:|:-----------|--------:|----------:|:----------|--------:|----------:|:----------|----------------:|:---------------|----------------------------:|
| No attack          |   1     |       0   | 12/12     |    1     |        0   | 12/12      |   0.977 |       4.5 | 12/12     |   1     |       0   | 12/12     |           0     | 12/12          |                    nan      |
| JPEG Q=90          |   0.947 |       5.5 | 12/12     |    0.952 |        3.9 | 12/12      |   0.79  |      25.4 | 3/12      |   0.947 |       5.4 | 12/12     |           0.501 | 0/12           |                      0.9933 |
| JPEG Q=70          |   0.901 |      14.4 | 8/12      |    0.909 |       11.5 | 10/12      |   0.717 |      33.3 | 0/12      |   0.901 |      14.3 | 8/12      |           0.5   | 0/12           |                    nan      |
| JPEG Q=50          |   0.886 |      16.1 | 8/12      |    0.895 |       14.2 | 8/12       |   0.668 |      37.3 | 0/12      |   0.886 |      16   | 8/12      |           0.5   | 0/12           |                    nan      |
| Gaussian v=0.001   |   0.998 |       0   | 12/12     |    0.998 |        0   | 12/12      |   0.938 |       8   | 12/12     |   0.998 |       0   | 12/12     |           0.5   | 0/12           |                    nan      |
| Gaussian v=0.01    |   0.989 |       1.4 | 12/12     |    0.992 |        0.8 | 12/12      |   0.955 |       5.3 | 12/12     |   0.989 |       1.4 | 12/12     |           0.499 | 0/12           |                      0.99   |
| Salt&Pepper d=0.01 |   0.979 |       3   | 12/12     |    0.985 |        1.9 | 12/12      |   0.945 |       6.3 | 12/12     |   0.979 |       3   | 12/12     |           0.499 | 0/12           |                      0.9841 |
| Avg blur 3x3       |   0.608 |      52.4 | 1/12      |    0.682 |       43.7 | 2/12       |   0.552 |      50.8 | 0/12      |   0.608 |      52.4 | 1/12      |           0.5   | 0/12           |                      0.9909 |
| Centre blank 6.25% |   0.559 |      42.5 | 0/12      |    0.602 |       39.5 | 1/12       |   0.945 |       7.7 | 12/12     |   0.559 |      42.5 | 0/12      |           0.464 | 4/12           |                      0.9869 |
| Scaling 0.5x->1x   |   0.604 |      53.7 | 2/12      |    0.688 |       43.2 | 2/12       |   0.593 |      47.8 | 0/12      |   0.604 |      53.7 | 2/12      |           0.5   | 0/12           |                      0.9957 |
| Rotation 2 deg     |   0.782 |      28.9 | 0/12      |    0.822 |       25.2 | 1/12       |   0.587 |      43.5 | 0/12      |   0.782 |      28.9 | 0/12      |           0.498 | 0/12           |                      0.9898 |
| Translation 2 px   |   0.999 |       0.1 | 12/12     |    0.999 |        0   | 12/12      |   0.74  |      29.6 | 0/12      |   0.999 |       0.1 | 12/12     |           0.501 | 0/12           |                      0.9781 |

Mean over 12 images. NCC of the extracted watermark from a never-watermarked image (JPEG-90 of the cover): 0.426 (BER 54.1%, decodes 0/12).

## Table 3: Hidden layer capacity and detectability

|   bpp | method   |   PSNR_RGB |   PSNR_G |   hist_chi2 |   recovered |   RS estimate |   P_E (SPAM) |
|------:|:---------|-----------:|---------:|------------:|------------:|--------------:|-------------:|
|  0.05 | adaptive |     68.925 |   64.154 |     117.291 |          11 |         0.034 |      nan     |
|  0.05 | random   |     68.928 |   64.157 |      10.659 |          11 |         0.061 |      nan     |
|  0.1  | adaptive |     65.9   |   61.129 |     138.987 |          11 |         0.049 |        0.397 |
|  0.1  | random   |     65.919 |   61.148 |      29.246 |          11 |         0.112 |        0.348 |
|  0.2  | adaptive |     62.903 |   58.131 |     168.122 |          11 |         0.083 |        0.374 |
|  0.2  | random   |     62.898 |   58.126 |      81.927 |          11 |         0.209 |        0.336 |
|  0.3  | adaptive |     61.151 |   56.379 |     192.667 |          11 |         0.13  |      nan     |
|  0.3  | random   |     61.14  |   56.369 |     149.934 |          11 |         0.305 |      nan     |
|  0.4  | adaptive |     59.888 |   55.116 |     226.564 |          11 |         0.199 |        0.338 |
|  0.4  | random   |     59.89  |   55.119 |     228.545 |          11 |         0.404 |        0.299 |

11 images (exp1_3_stego.csv) for PSNR/chi2/recovery; RS on 12 images; P_E preliminary (494 patches). RS estimate on covers alone: 0.022.

## Table 4: Security metrics

| item                             |   entropy |          chi2 |   corr_h |   corr_v |   corr_d |
|:---------------------------------|----------:|--------------:|---------:|---------:|---------:|
| Plain QR (watermark)             |    0.9951 |   8.37981e+06 |   0.884  |   0.8663 |   0.7574 |
| Scrambled QR (logistic map)      |    0.9951 |   8.37981e+06 |  -0.0013 |  -0.0028 |   0.0129 |
| AES-256-CBC ciphertext (payload) |    7.9975 | 227.914       |  -0.0126 |   0.0043 |  -0.011  |
| Plaintext payload (as bytes)     |    3.8573 |   1.19125e+06 |   0.1467 |  -0.1464 |  -0.2334 |

Differential/key tests: npcr_scramble = 0.0015; uaci_scramble = 0.0015; npcr_aes_first_byte = 99.5972; uaci_aes_first_byte = 33.3453; npcr_aes_last_byte = 0.0244; uaci_aes_last_byte = 0.0075; aes_wrongkey_bytes_differ_pct = 99.6109; logistic_wrong_x0_ber = 0.4972; logistic_right_x0_ber = 0.0000

## Table 5: Execution time

| Config   |   Embed (s) |   Extract (s) |
|:---------|------------:|--------------:|
| A        |       0.063 |         0.125 |
| A*       |       0.058 |         0.126 |
| B        |       0.117 |         0.169 |
| C        |       0.362 |         0.127 |

Python, single thread, cloud container; includes key/file I/O.

## Table 6: Ownership-claim tests (Config D)

| test                                                       | accepted   | reason                             |
|:-----------------------------------------------------------|:-----------|:-----------------------------------|
| Attacker's own certificate on our image (ambiguity attack) | 0/12       | no QR in image                     |
| Our certificate, owner field edited                        | 0/12       | signature invalid                  |
| Our parameters re-signed with attacker's key               | 0/12       | QR text does not match certificate |
| Owner certificate on unmarked cover                        | 0/12       | no QR in image                     |
| Owner certificate on unmarked cover, JPEG-90               | 0/12       | no QR in image                     |
| Legitimate owner on marked image                           | 12/12      | accepted                           |
| Overwrite attack: owner claim on re-marked image           | 0/12       |                                    |
| Overwrite attack: attacker claim on re-marked image        | 12/12      |                                    |
| Config A, same ambiguity attack (attacker's own U, V)      | 12/12      | attacker's QR decodes              |

Overwrite attack: PSNR of re-marked vs cover (dB): mean 39.96; Random logistic keys that yield ANY decodable QR (of 300, full decoder incl. shift search): 0


## Table 7: Robustness, Config A vs Config D at equal PSNR

| Attack             | A decodes   | D decodes   |   D module BER % |
|:-------------------|:------------|:------------|-----------------:|
| JPEG Q=90          | 12/12       | 12/12       |              0   |
| JPEG Q=70          | 8/12        | 12/12       |              0.2 |
| JPEG Q=50          | 8/12        | 12/12       |              0.8 |
| Gaussian v=0.001   | 12/12       | 12/12       |              0   |
| Gaussian v=0.01    | 12/12       | 3/12        |              6.9 |
| Salt&Pepper d=0.01 | 12/12       | 10/12       |              4.7 |
| Avg blur 3x3       | 1/12        | 12/12       |              0.4 |
| Centre blank 6.25% | 0/12        | 8/12        |              3.7 |
| Scaling 0.5x->1x   | 2/12        | 12/12       |              0.2 |
| Rotation 2 deg     | 0/12        | 0/12        |             39.9 |
| Translation 2 px   | 12/12       | 12/12       |              0.5 |

Mean PSNR: A 40.12 dB, D 40.00 dB; SSIM D 0.9906.
