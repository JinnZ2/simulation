# Shape specialization sim: same fault battery across the 5 platonic solids.
# Claim under test (notes/18 section 5): shapes specialize — octahedron wins axis-aligned
# faults, tetrahedron wins few-channel faults, high-vertex shapes win broadband faults.
# Refuted if: one shape wins >=3 of 4 fault classes (specialization is decorative).
import numpy as np, json

PHI = (1+np.sqrt(5))/2
SHAPES = {
 "tetra":  np.array([[1,1,1],[1,-1,-1],[-1,1,-1],[-1,-1,1]], float),
 "cube":   np.array([[s1,s2,s3] for s1 in (1,-1) for s2 in (1,-1) for s3 in (1,-1)], float),
 "octa":   np.array([[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]], float),
 "icosa":  np.array([[0,s1,s2*PHI] for s1 in (1,-1) for s2 in (1,-1)] +
                    [[s1,s2*PHI,0] for s1 in (1,-1) for s2 in (1,-1)] +
                    [[s2*PHI,0,s1] for s1 in (1,-1) for s2 in (1,-1)], float),
 "dodeca": np.array([[s1,s2,s3] for s1 in (1,-1) for s2 in (1,-1) for s3 in (1,-1)] +
                    [[0,s1/PHI,s2*PHI] for s1 in (1,-1) for s2 in (1,-1)] +
                    [[s1/PHI,s2*PHI,0] for s1 in (1,-1) for s2 in (1,-1)] +
                    [[s2*PHI,0,s1/PHI] for s1 in (1,-1) for s2 in (1,-1)], float),
}
for k in SHAPES:  # normalize circumradius
    SHAPES[k] /= np.linalg.norm(SHAPES[k][0])

def align(V, Vref):
    """Procrustes: center + optimal rotation (NO scale — strain must survive)."""
    A = V - V.mean(0); B = Vref - Vref.mean(0)
    U, _, Vt = np.linalg.svd(A.T @ B)
    R = U @ Vt
    if np.linalg.det(R) < 0: U[:, -1] *= -1; R = U @ Vt
    return A @ R

def metrics(V0, fault):
    V1 = V0 + fault(V0)
    A = align(V1, V0); B = V0 - V0.mean(0)
    disp = np.linalg.norm(A - B, axis=1)
    D = np.sqrt(np.mean(disp**2))          # detectability (per unit delta)
    L = disp.max()/max(np.median(disp), 1e-12)  # localization concentration
    return D, L

DELTA = 0.05
rng = np.random.default_rng(42)
base_noise = rng.normal(size=(20, 3)); base_noise /= np.linalg.norm(base_noise, axis=1, keepdims=True)

FAULTS = {
 "F1_axis_stretch":   lambda V: np.column_stack([V[:,0]*DELTA, 0*V[:,0], 0*V[:,0]]),
 "F2_single_vertex":  lambda V: np.eye(len(V))[0][:, None]*np.array([1,1,1])/np.sqrt(3)*DELTA,
 "F3_broadband":      lambda V: base_noise[:len(V)]*DELTA,
 "F4_single_strut":   lambda V: (-1)*np.eye(len(V))[0][:, None]*V[0]/np.linalg.norm(V[0])*DELTA,  # one vertex pulled inward = short strut
}

PREDICTED_WINNER = {"F1_axis_stretch": ("octa", "L"),      # vertices on axes concentrate strain
                    "F2_single_vertex": ("tetra", "D"),    # fewest channels, least dilution
                    "F3_broadband": ("dodeca", "D"),       # most vertices = most channels
                    "F4_single_strut": ("icosa", "L")}     # max readout bandwidth/localization

rows = {}
for fname, f in FAULTS.items():
    rows[fname] = {}
    for sname, V0 in SHAPES.items():
        D, L = metrics(V0, f)
        rows[fname][sname] = {"D": round(D, 5), "L": round(L, 3)}

print(f"{'fault':<18}{'shape':<9}{'D (detect)':<12}{'L (localize)':<12}")
for fname in FAULTS:
    for sname in SHAPES:
        r = rows[fname][sname]
        print(f"{fname:<18}{sname:<9}{r['D']:<12}{r['L']:<12}")
    print()

hits = 0; detail = []
for fname, (winner, met) in PREDICTED_WINNER.items():
    vals = {s: rows[fname][s][met] for s in SHAPES}
    actual = max(vals, key=vals.get)
    ok = actual == winner
    hits += ok
    detail.append(f"{fname}: predicted {winner} by {met}, actual {actual} -> {'HIT' if ok else 'MISS'}")
print("\n".join(detail))
# decorative check: does one shape win >=3 classes on BOTH metrics combined?
wins = {s: 0 for s in SHAPES}
for fname in FAULTS:
    for met in ["D", "L"]:
        vals = {s: rows[fname][s][met] for s in SHAPES}
        wins[max(vals, key=vals.get)] += 1
print("\nwin counts (of 8 metric-fault cells):", wins)
verdict = "SUPPORTED" if hits >= 3 and max(wins.values()) < 6 else \
          "REFUTED" if max(wins.values()) >= 6 or hits <= 1 else "INCONCLUSIVE"
print(f"\nVERDICT: {verdict}  (predicted-winner hits: {hits}/4; max single-shape wins: {max(wins.values())}/8)")
json.dump({"rows": rows, "hits": hits, "wins": wins, "verdict": verdict},
          open("/mnt/agents/output/sims/shape_specialization_results.json", "w"), indent=1)
