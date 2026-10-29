"""Config D evaluation: robustness (12 images x 12 attacks) and ownership-claim security tests."""
import copy
from run_ownership_cfg import *

rob, sec = [], []
for name in IMAGES:
    cover = load(name)
    D = O.embed_D(cover, m_own, X0_OWN, R_OWN, STEP, BLKD)
    for an in ATTACKS:
        atk = attack(an, D)
        txt, mm = O.extract_and_decode(atk, m_own.shape, X0_OWN, R_OWN, STEP, BLKD)
        acc, why = O.verify_claim(atk, cert_own, owner_key.publickey())
        rob.append(dict(config="D", image=LABEL.get(name, name), attack=an, psnr=calculate_psnr(cover, atk),
                        ssim=calculate_ssim(cover, atk), module_ber=float(np.mean(mm != m_own)),
                        decodes=txt is not None, owner_claim_accepted=acc))
    lab = LABEL.get(name, name)
    # 1. ambiguity attack: attacker presents own signed certificate + own key against OUR image
    acc, why = O.verify_claim(D, cert_atk, attacker_key.publickey())
    sec.append(dict(image=lab, test="Attacker's own certificate on our image (ambiguity attack)", accepted=acc, reason=why))
    # 2. forged certificate: our certificate with owner name changed, our signature kept
    f = copy.deepcopy(cert_own); f["body"]["owner"] = "Attacker Inc"
    acc, why = O.verify_claim(D, f, attacker_key.publickey())
    sec.append(dict(image=lab, test="Our certificate, owner field edited", accepted=acc, reason=why))
    # 3. copied parameters: attacker re-signs OUR parameters with THEIR key
    b = dict(cert_own["body"]); b["owner"] = OWNER; b["pk_fingerprint"] = O.fingerprint(attacker_key.publickey())
    c3 = dict(body=b, signature=pss.new(attacker_key).sign(SHA256.new(json.dumps(b, sort_keys=True).encode())).hex())
    acc, why = O.verify_claim(D, c3, attacker_key.publickey())
    sec.append(dict(image=lab, test="Our parameters re-signed with attacker's key", accepted=acc, reason=why))
    # 4. false alarm: our certificate against the unmarked cover (and its JPEG-90 copy)
    for tag, im in [("Owner certificate on unmarked cover", cover), ("Owner certificate on unmarked cover, JPEG-90", attack("JPEG Q=90", cover))]:
        acc, why = O.verify_claim(im, cert_own, owner_key.publickey())
        sec.append(dict(image=lab, test=tag, accepted=acc, reason=why))
    # 5. legitimate owner on the clean marked image
    acc, why = O.verify_claim(D, cert_own, owner_key.publickey())
    sec.append(dict(image=lab, test="Legitimate owner on marked image", accepted=acc, reason=why))
    # 6. overwrite attack: attacker embeds their own Config D mark on top of ours
    DD = O.embed_D(D, m_atk, X0_ATK, R_ATK, STEP, BLKD)
    sec.append(dict(image=lab, test="Overwrite attack: owner claim on re-marked image",
                    accepted=O.verify_claim(DD, cert_own, owner_key.publickey())[0], reason=""))
    sec.append(dict(image=lab, test="Overwrite attack: attacker claim on re-marked image",
                    accepted=O.verify_claim(DD, cert_atk, attacker_key.publickey())[0], reason=""))
    sec.append(dict(image=lab, test="Overwrite attack: PSNR of re-marked vs cover (dB)", accepted=None,
                    reason=f"{calculate_psnr(cover, DD):.2f}"))
    print(name, flush=True)

# 7. brute force: 2000 random logistic keys against one marked image
rng = np.random.default_rng(1)
D = O.embed_D(load("peppers"), m_own, X0_OWN, R_OWN, STEP, BLKD)
hits = 0
for _ in range(2000):
    t, _ = O.extract_and_decode(D, m_own.shape, float(rng.uniform(0.01, 0.99)), float(rng.uniform(3.57, 4.0)), STEP, BLKD)
    hits += t is not None
sec.append(dict(image="peppers", test="Random logistic keys that yield ANY decodable QR (of 2000)", accepted=None, reason=str(hits)))
pd.DataFrame(rob).to_csv(OUT / "robustness_D.csv", index=False)
pd.DataFrame(sec).to_csv(OUT / "ownership_tests.csv", index=False)
print("done")
