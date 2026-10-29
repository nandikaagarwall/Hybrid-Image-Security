**Table 5. Security of the encryption and scrambling components.**

| Component                                | Metric                                                  | Value                                           | Ideal               |
|:-----------------------------------------|:--------------------------------------------------------|:------------------------------------------------|:--------------------|
| AES-256-CBC ciphertext                   | Entropy (bits/byte)                                     | 7.9975                                          | 8                   |
| AES-256-CBC ciphertext                   | χ² of byte histogram                                    | 227.9                                           | < 293.25 (α = 0.05) |
| AES-256-CBC ciphertext                   | Adjacent-byte correlation H / V / D                     | -0.013 / 0.004 / -0.011                         | 0                   |
| AES-256-CBC ciphertext                   | NPCR / UACI, 1-bit change in first byte                 | 99.60% / 33.35%                                 | 99.61% / 33.46%     |
| AES-256-CBC ciphertext                   | Bytes changed by a 1-bit change in the AES key          | 99.61%                                          | ≈ 99.6%             |
| Logistic-map scrambling (base scheme QR) | Adjacent-pixel correlation H / V / D, plain → scrambled | 0.884 → -0.001 / 0.866 → -0.003 / 0.757 → 0.013 | → 0                 |
| Logistic-map key                         | Watermark BER with x0 changed by 10⁻¹⁰                  | 0.497                                           | 0.5                 |
| Proposed watermark key                   | Random (r, x0) keys that yield any decodable QR         | 0 of 300                                        | 0                   |

AES metrics on 64 KiB of ciphertext (the 64-byte message alone is too short for byte statistics). NPCR for a change in the LAST byte is 0.02%, as expected for CBC, which propagates changes forward only.