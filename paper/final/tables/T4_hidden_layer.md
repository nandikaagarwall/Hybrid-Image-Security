**Table 4. Hidden-layer capacity and detectability (texture-ranked LSB vs random LSB).**

|   Payload (bpp) |    Bits |   Green PSNR (dB) |   RGB PSNR (dB) | Message recovered   | RS estimate: ours   |   RS estimate: random LSB | P_E: ours   | P_E: random LSB   |
|----------------:|--------:|------------------:|----------------:|:--------------------|:--------------------|--------------------------:|:------------|:------------------|
|            0.05 |  13,107 |             64.15 |           68.93 | 11/11               | **0.034**           |                     0.061 | –           | –                 |
|            0.1  |  26,214 |             61.13 |           65.9  | 11/11               | **0.049**           |                     0.112 | **0.397**   | 0.348             |
|            0.2  |  52,428 |             58.13 |           62.9  | 11/11               | **0.083**           |                     0.209 | **0.374**   | 0.336             |
|            0.3  |  78,643 |             56.38 |           61.15 | 11/11               | **0.130**           |                     0.305 | –           | –                 |
|            0.4  | 104,857 |             55.12 |           59.89 | 11/11               | **0.199**           |                     0.404 | **0.338**   | 0.299             |

RS estimate = embedding rate inferred by RS steganalysis (closer to the true payload = easier to detect; on covers: 0.022). P_E = detection error of a SPAM-686 + random-forest detector (0.5 = undetectable; preliminary, 494 patches). Actual message: 340 bytes = 2,720 bits; padded with random bits to the stated payload.