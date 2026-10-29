**Table 8. Computational cost and key material.**

| Scheme          |   Embed (s) |   Extract (s) | What the verifier needs                                       |
|:----------------|------------:|--------------:|:--------------------------------------------------------------|
| Base scheme (A) |       0.063 |         0.125 | cover image + U, V matrices (2 × 256 × 256 floats)            |
| Proposed        |       0.291 |         1.544 | signed certificate (< 1 KB) + RSA private key for the message |

Mean over 12 images, Python on a single CPU core. Proposed extract time includes the hidden message and certificate check; it rises when the decoder has to search for a shift.