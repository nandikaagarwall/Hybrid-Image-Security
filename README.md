# Hybrid Image Security: simulation project

Encryption + steganography + DWT-SVD watermarking.
Base paper: Sanivarapu et al., *Applied Sciences* 12(17), 8724, 2022.

This repo already contains the Phase 0 foundation: the folder layout, shared config, shared metrics (tested), interface contract and setup check. Follow the steps below **in order**. Don't skip ahead.

```
hybrid-image-security/
├── data/standard/      ← the 12 standard colour images go here
├── data/bossbase/      ← BOSSbase .pgm files (Person B, not committed to git)
├── keys/               ← RSA keys, generated ONCE
├── results/tables/     ← CSVs of every experiment
├── results/figures/    ← plots
├── src/
│   ├── config.py       ← EVERY parameter lives here
│   ├── io_utils.py     ← load/save images (always PNG)
│   ├── metrics.py      ← all metrics, shared by both of you
│   └── interfaces.py   ← the function signatures you both agreed on
└── scripts/
    ├── check_setup.py  ← run after setup; must say PASS
    └── make_keys.py    ← run once
```

---

## PHASE 0: do this together, sitting side by side

### Step 0.1: Install Python and the project (both of you, ~20 min)

1. Install **Python 3.11 or 3.12** from python.org. On Windows, tick "Add Python to PATH".
2. Install **Git** from git-scm.com, and **VS Code** if you don't have it.
3. Unzip this folder somewhere without spaces in the path (e.g. `D:\projects\hybrid-image-security`).
4. Open a terminal in that folder and create a virtual environment:
   - Windows: `python -m venv .venv` then `.venv\Scripts\activate`
   - Mac/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
5. `pip install -r requirements.txt`
6. QR decoding needs the zbar library:
   - Windows: nothing extra (bundled with pyzbar).
   - Mac: `brew install zbar`
   - Ubuntu: `sudo apt install libzbar0`
7. Run `python scripts/check_setup.py`. Everything should PASS except the three data/keys lines. Those get fixed in the next steps.

### Step 0.2: Shared GitHub repo (one person creates it, ~10 min)

1. Person A: on github.com create a **private** repo `hybrid-image-security` and add Person B as a collaborator.
2. Person A, in the folder:
   ```
   git init
   git add .
   git commit -m "Phase 0 skeleton"
   git branch -M main
   git remote add origin https://github.com/<username>/hybrid-image-security.git
   git push -u origin main
   ```
3. Person B: `git clone <repo url>`, then repeat Step 0.1 steps 4–7 inside the clone.
4. Working rule: each person works on their own branch (`git checkout -b track-a` / `track-b`) and merges into `main` only when their code runs. **Never** edit `config.py` or `metrics.py` alone; agree first.

### Step 0.3: Lock the design decisions (~15 min, discuss)

Open `src/config.py` and read every value aloud together. Confirm or change:

| Decision | Default set | Why |
|---|---|---|
| Watermark channel | Blue (2) | Same as base paper |
| Hidden layer channel | Green (1) | Never collides with the watermark |
| Wavelet | `haar` | **Check the base paper's methodology section**; use whatever wavelet they name |
| Logistic map r, x₀ | 3.99, 0.31415… | Must stay in the chaotic range (3.57, 4] |
| Owner text | your names + India | Goes into the QR |
| Attack parameters | listed in `ATTACKS` | Same for both tracks |

Then write the decisions into the **Decision log** at the bottom of this README and commit. Your professor will ask "why did you choose X". This log is your answer.

### Step 0.4: Get the 12 standard images (Person A, ~20 min)

1. Open the base paper and find the figure or table listing its **12 test images**. Write their names in the decision log.
2. Download them from the **USC-SIPI Image Database** (search "USC-SIPI image database misc"). Most standard 512×512 colour images (Baboon/Mandrill, Peppers, Airplane/F-16, House, Sailboat, Splash, Tiffany…) are in the "Miscellaneous" volume as `.tiff`.
3. If any image the paper used isn't available, substitute another standard 512×512 colour image and **log the substitution**.
4. Put all 12 in `data/standard/`, renamed as `01_baboon.tiff`, `02_peppers.tiff`, etc. (the number prefix keeps the order fixed).
5. Commit them (they're small).

### Step 0.5: Get BOSSbase (Person B, start the download now, it's large)

1. Search "BOSSbase 1.01 download". It's hosted by the Binghamton DDE lab. It's 10,000 grayscale 512×512 `.pgm` images (~1.4 GB zipped).
2. Unzip into `data/bossbase/` (the folder is in `.gitignore`, so it won't go to GitHub; each person who needs it downloads it).
3. You only need the first 2,000 for now (`BOSS_SUBSET` in config).
4. Note for later: BOSSbase is grayscale. Because the hidden layer only touches the green channel and the watermark never does, a BOSSbase image can stand in for the green channel in Experiment 2. Write this reasoning in the decision log.

### Step 0.6: Generate keys once (Person A, 1 min)

```
python scripts/make_keys.py
git add keys/ && git commit -m "RSA keys (fixed for all experiments)" && git push
```
Person B: `git pull`. **Nobody regenerates keys after this.**

### Step 0.7: Final check (both)

`python scripts/check_setup.py` → BOSSbase may still FAIL for Person A (fine); everything else must PASS.

### Step 0.8: Read the contract (both, 10 min)

Read `src/interfaces.py` together. These four functions are how your code plugs together:

- Person A writes `src/watermark.py` with `embed_watermark` / `extract_watermark`.
- Person B writes `src/payload.py` with `embed_payload` / `extract_payload`.
- Inputs and outputs are always `uint8` RGB `(512, 512, 3)`.
- Save results as **PNG only**. A JPG save silently destroys the embedded bits.

**Phase 0 is done.** Split up.

---

## PHASE 1: first tasks for each track

### Person A: start with A1 (watermark preparation)

Create `src/watermark.py`. Build and test each function on its own before moving on.

**A1. `make_qr(text) -> uint8 256×256, values 0/255`**
- Use `qrcode` with `box_size=1, border=4`, then resize to 256×256 with `INTER_NEAREST` (copy from `check_setup.py`).
- Test: `metrics.qr_decodes(qr, config.OWNER_TEXT)` returns True.

**A2. `rsa_encrypt_qr(qr, pubkey)` / `rsa_decrypt_qr(...)`**
- The base paper RSA-encrypts the QR. First re-read exactly *how*: per pixel? per block? the text before QR generation? Write your interpretation in the decision log.
- Test: decrypt(encrypt(qr)) == qr exactly.

**A3. `logistic_scramble(img, r, x0)` / `logistic_unscramble(...)`**
- Generate a sequence of 256×256 values with `x = r*x*(1-x)` (discard the first `LOGISTIC_DISCARD` values) and `perm = np.argsort(seq)`.
- Scramble: `flat[perm]`. Unscramble: `out[perm] = scrambled_flat`.
- Test 1: unscramble(scramble(qr)) == qr.
- Test 2: run `metrics.corr_all` on the QR vs. the scrambled QR. Correlation should fall from ~0.9 to ~0. **Save these numbers. They're Experiment 5 data.**
- Test 3: `metrics.entropy` and the histogram of the QR vs. the scrambled QR will be **identical** (permutation only). Save this too; it's an expected weakness.

**A4. Config A embedding** (only after A1–A3 pass)
- Blue channel → `pywt.dwt2(..., config.WAVELET)` → `np.linalg.svd(LL)` → modify S using the base paper's rule with `ALPHA_FIXED` → inverse SVD → `pywt.idwt2` → clip to uint8.
- Tune `ALPHA_FIXED` until PSNR on the 12 images is 40–44 dB, then freeze it in config.

### Person B: start with B1 (payload encryption)

Create `src/payload.py`.

**B1. `encrypt_payload(message, pubkey) -> bits`**
- Generate a random AES-256 key with `Crypto.Random.get_random_bytes(32)`.
- Encrypt the message with **AES-GCM**: you get the ciphertext, a nonce and a tag.
- Encrypt the AES key with **RSA-OAEP** (`PKCS1_OAEP`) using `keys/rsa_public.pem`.
- Pack into one byte string: `len(rsa_key_blob) | rsa_key_blob | nonce | tag | ciphertext`.
- Convert to bits: `np.unpackbits(np.frombuffer(blob, np.uint8))`.
- Test: `decrypt_payload(bits, privkey) == message`.

**B2. Payload sized by bits per pixel**
- For capacity tests you need *n* bits = bpp × 512 × 512. Pad the encrypted blob with random bytes up to *n* bits (the length header tells the decoder where the real data ends).
- Test: for every value in `PAYLOAD_BPP`, encode → decode returns the message.

**B3. Naive baseline: `lsb_replacement` embed/extract in the green channel**
- Pick pixel positions with a seeded permutation (`np.random.default_rng(seed).permutation`), then set the LSB to each bit.
- Test: extracted bits == embedded bits (BER = 0), and PSNR ≥ 50 dB.

**B4. Texture-adaptive embedding**
- `pip install conseal` and check its docs for WOW / S-UNIWARD / HILL (they give a cost map; you simulate or embed with ±1).
- If its API doesn't fit, build your own: texture map = local variance in a 3×3 window → embed ±1 (LSB matching) only in the top-texture pixels.

**B5. Start Experiment 2 early**
- Write a SPAM feature extractor (686-D, second-order SPAM) or check whether `conseal` / other libraries provide one.
- Extract features for 2,000 BOSSbase covers now (it's slow; let it run overnight).

---

## Results format (both, from the first experiment onward)

- One CSV per experiment in `results/tables/`, one row per (image, config, attack, parameter).
- Columns e.g. `image, config, attack, param, psnr, ssim, ncc, ber, qr_ok, entropy, ...`
- Use `metrics.mean_std()` for the summary tables in the slides.
- Never overwrite a results CSV. Add a date to the filename.

---

## Decision log

Fill this in as you go. Every row = one choice your professor might question.

| Date | Decision | Reason | Who |
|---|---|---|---|
| | Watermark in blue, hidden layer in green | Layers can't overwrite each other; tracks can run in parallel | both |
| | Wavelet = ? | Base paper section ? | |
| | 12 images = ? | Base paper Fig/Table ? | |
| | RSA applied to QR how? | Base paper section ? | |
| | AES-GCM + RSA-OAEP for payload | RSA alone can't encrypt long messages; GCM also authenticates | |
| | BOSSbase grayscale used as green channel | Watermark never touches green | |
