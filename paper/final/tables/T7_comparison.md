**Table 7. Comparison with the base paper (mean NCC over 12 images).**

| Method                               |   PSNR (dB) |   NCC: JPEG 90 |   NCC: Gauss 0.01 |   NCC: S&P |   NCC: Blur 3×3 |   NCC: Scale 0.5 |   NCC: Rot. 2° |   NCC: Shift 2 px | Blind extraction   | False-ownership attack   |
|:-------------------------------------|------------:|---------------:|------------------:|-----------:|----------------:|-----------------:|---------------:|------------------:|:-------------------|:-------------------------|
| Sanivarapu et al. 2022 (as reported) |       42.45 |          0.993 |             0.99  |      0.984 |           0.991 |            0.996 |          0.99  |             0.978 | no                 | not evaluated            |
| Same scheme, our reproduction (A)    |       40.12 |          0.947 |             0.989 |      0.979 |           0.608 |            0.604 |          0.782 |             0.999 | no                 | fails (12/12)            |
| **Proposed**                         |       40.19 |          1     |             0.908 |      0.918 |           0.993 |            0.996 |          0.568 |             0.987 | yes                | passes (0/12)            |
| [Paper 2 — to add]                   |             |                |                   |            |                 |                  |                |                   |                    |                          |
| [Paper 3 — to add]                   |             |                |                   |            |                 |                  |                |                   |                    |                          |

Base-paper attack sizes for cropping and rotation are not stated, and its salt & pepper density is stated as 0.5; our settings are in Table 1. Centre blanking is omitted here for that reason (see Table 3).