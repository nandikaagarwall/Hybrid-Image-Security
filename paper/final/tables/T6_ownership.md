**Table 6. Ownership-verification tests (12 images each).**

| Claim                                                     | Base scheme (A): accepted   | Proposed: accepted         | Correct outcome         |
|:----------------------------------------------------------|:----------------------------|:---------------------------|:------------------------|
| Real owner claims the marked image                        | 12/12                       | 12/12                      | accept                  |
| Attacker presents their own keys (false-ownership attack) | 12/12                       | **0/12**                   | reject                  |
| Owner's certificate with the owner name edited            | no certificate              | 0/12                       | reject                  |
| Owner's parameters re-signed with the attacker's key      | no certificate              | 0/12                       | reject                  |
| Owner's claim on an image never watermarked               | 0/12                        | 0/12                       | reject                  |
| Same, after JPEG-90                                       | –                           | 0/12                       | reject                  |
| Attacker re-watermarks the image with their own mark      | –                           | attacker 12/12, owner 0/12 | needs trusted timestamp |

The overwrite attack is not prevented by any blind scheme alone; the standard remedy is a trusted timestamp on the signed certificate (first registration wins).