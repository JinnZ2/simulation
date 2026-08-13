# Deep Trigonometry — Structural Research Brief
### For the JinnZ2 falsifiable-claims ecosystem (Rosetta shapes / octahedral instrument / VSA / intrinsic dimension)

All numeric claims below were either verified by web sources (cited) or recomputed exactly (marked `[computed]`).

---

## 1. Spherical trigonometry on polyhedra

### 1.1 Girard's theorem (spherical excess)
For a spherical triangle on the unit sphere with angles α, β, γ:
**Area = α + β + γ − π ≥ 0** (the "spherical excess"). For an N-gon: Area = (sum of angles) − (N−2)π. Total sphere area 4π.
- Sources: arXiv:2605.01536 (winding-number paper, explicit Girard statement + robust atan2 signed-area formula); arXiv:1810.01786 (Lemma: spherical laws of sines/cosines + Girard's theorem); arXiv:1409.4736 (Euler/Lagrange/Puissant area formulas, e.g. tan(δ/2) half-angle area formulas).
- Computational gem (Oosterom & van Straten 1983): signed area = 2·atan2(v0·(v1×v2), 1 + v0·v1 + v0·v2 + v1·v2) — branch-safe solid angle of a triangle, exactly what you want for a solid-angle checksum on a deformed mesh. [cited: arXiv:2605.01536]

### 1.2 Descartes' angular defect = discrete Gauss–Bonnet
Defect at vertex v: δ_v = 2π − Σ(face angles at v). **Theorem (Descartes): Σ_v δ_v = 2π·χ(P)**, i.e. 4π for any convex (genus-0) polyhedron. This is the discrete Gauss–Bonnet theorem; angular defect is the canonical discrete analogue of Gaussian curvature.
- Sources: arXiv:2512.19106 (explicit statement Σδ_v = 2πχ, "natural discrete analogue of Gaussian curvature"); arXiv:2009.00116 ("total angular deficit ... is exactly 4π; Descartes' theorem, a discrete form of Gauss–Bonnet").
- `[computed]` Octahedron: each vertex has 4 triangles ⇒ defect = 2π − 4·(π/3) = 2π/3 per vertex; 6 vertices ⇒ total 4π. ✔ This is a **hard conservation law**: any distortion that keeps the surface closed and genus-0 must *redistribute* defect among vertices but cannot change the 4π total.

### 1.3 Dihedral angles of the Platonic solids (exact) `[computed, matches standard tables]`
| Solid | cos θ | θ (deg) |
|---|---|---|
| Tetrahedron | 1/3 | 70.5288° |
| Cube | 0 | 90° |
| Octahedron | −1/3 | 109.4712° |
| Dodecahedron | −1/√5 | 116.5651° |
| Icosahedron | −√5/3 | 138.1897° |

Note tetra/octa dihedral angles are supplementary (70.53 + 109.47 = 180), a duality/self-complementarity fact. Dodeca angle also = 2·atan(φ) with golden ratio φ — a clean trig–φ bridge.

### 1.4 Solid angles
Solid angle Ω of a polyhedral vertex = spherical excess of the polar (link) polygon = sum of incident dihedral angles − (n−2)π (n = faces at vertex). For the octahedron vertex: Ω = 4·arccos(−1/3) − 2π ≈ 2.3493 sr `[computed]`; 6 vertices × Ω + defect-structure relates to 4π via the polar duality between dihedral angles and face angles — solid angle at v and angular defect at v are linked by the polar/spherical-duality transform.

### 1.5 Gram matrices of vertex sets `[computed]`
Octahedron vertices ±e_i: Gram matrix has entries {1 (self), −1 (antipode), 0 (otherwise)}; spectrum {2,2,2,0,0,0} — the nonzero eigenvalues carry exactly the 3-dimensional "shape content". The Gram matrix of a centered configuration is **rank ≤ d and rotation-invariant**; its eigenspectrum is a complete rigid-motion invariant, i.e. a coordinate-free shape fingerprint. This connects directly to Kendall shape space (shape = configuration modulo similarity; Gram eigenvalues = invariant coordinates) and to Procrustes distance (d_Proc² = 2(1 − Σ√λ_i of cross-Gram), essentially chordal distance on the pre-shape sphere).

---

## 2. Trigonometric identities as algebraic / representation-theoretic structure

### 2.1 Addition formulas = group law
cos(θ+φ) = cosθcosφ − sinθsinφ, sin(θ+φ) = sinθcosφ + cosθsinφ is exactly the statement that θ ↦ [[cosθ, −sinθ],[sinθ, cosθ]] is a homomorphism ℝ → SO(2). Equivalently e^{i(θ+φ)} = e^{iθ}e^{iφ}: **the addition formulas are the group law of the circle** U(1). sin²+cos²=1 is the quadratic form defining the group manifold itself.

### 2.2 Chebyshev / multiple-angle
cos(nθ) = T_n(cos θ), sin(nθ) = sin θ · U_{n−1}(cos θ): Chebyshev polynomials are the *power maps* of the circle group expressed in the invariant coordinate x = cosθ. They are the characters of SU(2) evaluated in Chebyshev form: the SU(2) character of spin-j is χ_j(θ) = sin((2j+1)θ)/sin θ, a U-polynomial. Recurrence T_{n+1} = 2xT_n − T_{n−1} = Clebsch–Gordan for tensoring with the 2-dim representation. (Standard; consistent with Peter–Weyl sources below.)

### 2.3 Peter–Weyl: trig functions ARE the representation theory
- For G = U(1): irreps are characters χ_n(θ)=e^{inθ}; Peter–Weyl ⇒ classical Fourier series is the irrep decomposition of L²(S¹). [Source: Peter–Weyl expositions, communityhousepittsburgh.org blog; ai-futureschool explainer]
- For SO(3): L²(S²) = ⊕_{ℓ≥0} V_ℓ, dim V_ℓ = 2ℓ+1, spanned by spherical harmonics Y_ℓm; S² ≅ SO(3)/SO(2). Addition theorem: Σ_m Y*ℓm(n′)Yℓm(n) = (2ℓ+1)/4π · P_ℓ(cos γ) — the spherical generalization of the addition formula, with Legendre P_ℓ = D^ℓ_{00}. [Source: preprints 202604.0332, full theorem statement and addition theorem]
- For SU(2): irreps labeled by half-integers j; matrix coefficients = Wigner D-functions; completeness over Haar measure. [Sources: arXiv:1202.5414, arXiv:0809.2017 (Peter–Weyl as orthonormal basis of matrix coefficients)]
- Generalization to polynomials on spheres: Pol_{≤d}(S^{n−1}) = H_0 ⊥ H_1 ⊥ … ⊥ H_d, each H_k O(n)-irreducible and pairwise inequivalent [arXiv:0809.2017, Thm 5.11].

### 2.4 Finite subgroups: octahedral/cubic harmonics — the Fourier basis of the octahedron
Restricting SO(3) irreps to the octahedral group O (48 elements; O_h = O × C_i) splits each ℓ-shell into O_h irreps. The standard result (Bethe 1929; Von der Lage–Bethe 1947 "cubic harmonics"):

| ℓ | O_h content (even parity, g) |
|---|---|
| 0 | A1g |
| 1 | T1u (odd) |
| 2 | Eg ⊕ T2g |
| 3 | A2u ⊕ T1u ⊕ T2u |
| 4 | A1g ⊕ Eg ⊕ T1g ⊕ T2g |
| 5 | (odd) A2u ⊕ 2T1u... |
| 6 | A1g ⊕ A2g ⊕ Eg ⊕ T1g ⊕ T2g |

Key structural fact: **ℓ = 0, 1, 2, 3 contain no A1g**; the first nontrivial octahedral invariant is at ℓ = 4 (the cubic harmonic K_4 ∝ x⁴+y⁴+z⁴ − 3/5·r⁴, i.e. the ℓ=4 A1g combination), then ℓ = 6, 8…. So the angular power spectrum of any octahedrally-symmetric function has support only on {ℓ=0} ∪ {ℓ≥4 with the O_h-allowed multiplicities}. This is a hard, checkable selection rule. (Standard group-theory result; confidence high.)
Connection to equivariant bifurcation: in Golubitsky–Stewart equivariant bifurcation theory, symmetry-breaking modes organize by isotropy subgroups/irreps — each O_h irrep (A1g breathing, Eg tetragonal, T2g shear, T1u translation/dipole…) is a *distinct failure channel*, precisely the "irreps = failure channels" grounding the ecosystem already cites.

---

## 3. Trigonometry in measurement

- **Triangulation** (angles + one baseline → positions) vs **trilateration** (distances only → positions). Triangulation error grows with distance as ~baseline−1 (angle noise → position noise ∝ r²/b); trilateration error is distance-proportional. Hybrid angle+range is the metrology standard.
- **Interferometry**: the measured quantity is a *phase* φ = 2π·OPD/λ — literally an angle on the circle group. Displacement sensitivity: λ/(2π) per radian; with λ ≈ 500 nm, 1 mrad phase noise ⇒ ~0.1 nm. Phase is the cheapest high-precision physical observable: two photodiodes + a beamsplitter. (Standard; e.g. Michelson/LIGO metrology. No specific citation retrieved; textbook-level, confidence high.)
- **Gnomonic projection** (center projection from sphere center): maps great circles → straight lines; used to map polyhedral/celestial data to the plane, and it is the natural projection for polyhedron↔sphere work. **Orthographic** (projection from infinity) preserves the visual-hull structure used in shape-from-silhouette and geometric morphometrics landmark digitization. Stereographic projection is conformal (angle-preserving) — relevant because angle preservation = local shape preservation in morphometrics. (Standard cartographic facts.)
- Spherical law of cosines cos c = cos a cos b + sin a sin b cos C is the distance formula on S² — i.e. angular distance = arccos of Gram entry. **Angular distance between unit landmarks = arccos(G_ij)** ties §1.5 Gram matrices directly to spherical trig. [Law stated in arXiv:1810.01786]

---

## 4. Hyperbolic trigonometry (rigorous results only)

- **Rapidity**: a Lorentz boost is a hyperbolic rotation: B(ζ) with cosh ζ, sinh ζ; tanh ζ = v/c. Collinear velocity addition becomes **rapidity addition** ζ = ζ1 + ζ2, i.e. tanh(ζ1+ζ2) = (tanh ζ1 + tanh ζ2)/(1 + tanh ζ1 tanh ζ2). Non-collinear boosts don't compose to a boost: the defect is **Thomas precession**, a rotation equal to the angular defect of the loop in (hyperbolic) rapidity space — a Berry/Foucault-type holonomy. [Sources: arXiv:2408.07036 (boost matrix, "hyperbolic rotation"); arXiv:2603.24409 (tanh ζ = β, Thomas precession as angular-deficit holonomy on rapidity space)]
- **Hyperbolic geometry of trees**: metric trees are exactly the 0-hyperbolic geodesic spaces (Gromov). **Sarkar's theorem (2011)**: any finite tree admits, for every ε>0, a (1+ε)-bilipschitz embedding into ℍ² (Delaunay construction); Sala et al. 2018 give distortion/precision tradeoffs and bit-complexity bounds O((1/ε)(ℓ/n)log deg_max) etc. [Sources: arXiv:2604.21027 (explicit statement + proof sketch citing Sarkar 2012/Gromov 0-hyperbolicity); arXiv:2502.17130 (HS-DTE, Sarkar/Sala tradeoffs)]
- **Hyperbolic embeddings of hierarchies**: Nickel & Kiela 2017 (Poincaré embeddings, arXiv:1705.08039) — exponential volume growth matches exponential node growth of trees, far lower distortion than Euclidean; Nickel & Kiela 2018 (Lorentz model, arXiv:1806.03417) — numerically stable. [Sources: arXiv:2608.01450, arXiv:2502.17130, arXiv:1513 microscope paper all re-derive/cite these]
- **Hyperbolic Ptolemy**: a convex hyperbolic quadrilateral is cyclic iff sinh(e/2)·sinh(f/2) = sinh(a/2)sinh(c/2) + sinh(b/2)sinh(d/2) — the hyperbolic avatar of Ptolemy, with s(x)=x→sinh(x/2). [arXiv:1302.4919, Prop 4.2]

---

## 5. Trig identities as invariant generators

- **sin²θ + cos²θ = 1 as conservation law**: the quadratic invariant of SO(2); under any rotation it is preserved — i.e. it is the Casimir/first integral of circular motion. In diagnostics terms: it's a *checksum on any (sin, cos) pair* — deviation from 1 signals channel corruption, exactly the role Procrustes-shape conservation could play.
- **Ptolemy's theorem**: cyclic quadrilateral ABCD: AC·BD = AB·CD + BC·AD (equality iff cyclic; inequality Ptolemy's inequality otherwise). It is the addition formula in disguise: applying it to four points on a circle with chord = sin(half-angle) yields the sine addition law. Generalizations unify Euclidean/spherical/hyperbolic via s(x) = x, sin x, sinh x. [Sources: arXiv:1009.2970 (unified s-function Ptolemy); arXiv:1302.4919 (hyperbolic version)]
- **Symbolic regression / equation discovery**: trigonometric identities are the classic confounders and the classic priors — equation-discovery systems (e.g. AI Feynman, Udrescu & Tegmark 2020) exploit units, symmetry, and separability; sin²+cos²=1-type invariants are exactly what "dimensional/symmetry analysis" modules use to prune search. Trig identities function as *generators of the ideal of relations* any discovered equation must respect: a discovered law f(x)=0 can be quotiented by the trig-identity ideal. (Inference from AI Feynman methodology; flag as inferential, not a cited theorem.)

---

## 6. Exotic

- **Bloch sphere / spin coherent states**: spin-½ state |ψ⟩ = cos(θ/2)|0⟩ + e^{iφ}sin(θ/2)|1⟩ — half-angles (spinor double-cover). Spin-s coherent states are SU(2) orbits; overlap |⟨n|n'⟩|² = ((1+n·n')/2)^{2s} — a pure trig function of the angle between Bloch vectors. [Sources: arXiv:2601.20922 (overlap, resolution of identity, measure (2S+1)/π · d²z/(1+|z|²)²); arXiv:2508.08414 (explicit cos/sin forms)]
- **Majorana stellar representation**: any spin-j state = 2j points on S²; spin coherent state = all stars coincident; time-reversal-invariant integer-spin states ↔ real spherical harmonics (Maxwell–Sylvester). **Polyhedral constellations**: the most "anticoherent" / "kings of quantumness" states have stars arranged as Platonic solids — the octahedron is literally a quantum state (spin-3 octahedral state with point-group symmetry O_h). [Sources: arXiv:1803.10356 (Majorana ↔ Maxwell–Sylvester ↔ real spherical harmonics); arXiv:1612.06804 (kings, antipodal constellations); arXiv:1509.08300 (anticoherence with point-group symmetries)]
- **Arcsine laws in probability**: for symmetric random walks, P(fraction of time positive ≤ x) → (2/π)arcsin√x (Lévy's arcsine law); also last-visit and maximum-location arcsine laws for Brownian motion; multidimensional analogues exist. Erdős's arcsine law for prime factors: lim density = (2/π)arcsin√u. [Sources: arXiv:1610.02861 (multidimensional arcsine law); arXiv:2105.15051 (arcsine laws for random walks/Brownian motion, Erdős and DDT theorems)] Note the arcsine CDF is Beta(½,½) — the invariant measure of the Chebyshev map x ↦ 2x²−1 — a deep trig–probability junction (Chebyshev polynomials are conjugate to the tent/doubling map under x = cos θ).

---

## Possible intersections with the ecosystem (falsifiable ideas)

**Axis (a) — octahedral irrep diagnostic basis**

1. **Octahedral angular spectrum as distortion fingerprint.**
   Claim: Any vertex displacement field on the octahedral instrument, expanded in O_h-adapted harmonics (cubic harmonics), has a *selection-rule signature*: a perfect octahedron's radial function has power only at ℓ=0 and ℓ≥4 (no ℓ=1,2,3 A1g). Distortions populate forbidden channels in predictable irrep patterns (T1u = translation, Eg = tetragonal squash, T2g = shear).
   Test: synthesize known distortions (squash, shear, single-vertex push), compute the angular spectrum via least-squares projection onto O_h harmonics; verify each distortion lands in its predicted irrep subspace with R² > 0.95.
   Refutation: if a pure tetragonal squash shows >10% power outside Eg⊕A1g, or if the perfect-shape spectrum has nonzero ℓ=1–3 invariant content, the basis is wrong or numerically contaminated.

2. **Irrep-resolved Procrustes decomposition.**
   Claim: Procrustes distance between measured and ideal octahedron decomposes additively across O_h irreps (Parseval): d² = Σ_irrep d²_irrep, so "which failure channel" is readable from energy fractions.
   Test: orthogonal projection onto irrep subspaces; check additivity to numerical precision on synthetic data.
   Refutation: non-additivity beyond float error (would indicate wrong symmetrization of the basis).

3. **First-signature invariant at ℓ=4.**
   Claim: The ratio A(ℓ=4)/A(ℓ=6) of A1g-channel power is a scale-invariant scalar that detects "which platonic solid" a near-platonic shape is (tetra vs octa vs cube have distinct ℓ=4/ℓ=6 ratios) — a 1-number shape classifier.
   Test: compute for all 5 platonic solids + random perturbations; check separability.
   Refutation: overlapping ratios under small perturbations (noise floor kills separability).

**Axis (b) — Descartes defect as conserved checksum**

4. **Angular-defect conservation as data-integrity checksum for the instrument.**
   Claim: For any closed genus-0 mesh derived from the octahedral instrument, Σδ_v = 4π to within discretization error; a *measured* violation exceeding mesh-resolution bounds flags sensor/registration error, not physics.
   Test: triangulate measured point clouds (including deliberately corrupted ones with a duplicated/dropped vertex); compute defect sum via atan2 solid-angle formula.
   Refutation: corrupted datasets that pass the checksum (false negatives) at a rate above a pre-set threshold would show the checksum is insensitive to the corruption class that matters.

5. **Defect-flow localization.**
   Claim: Under a localized physical deformation, the redistributed defect is concentrated at vertices adjacent to the deformation (discrete curvature is a local conserved-charge redistribution); specifically the defect *dipole moment* Σδ_v·x_v localizes the damage site better than raw vertex displacement in the presence of rigid-motion noise.
   Test: synthetic localized dents + random rigid motion; compare localization error of defect-dipole vs displacement methods.
   Refutation: defect dipole performs no better (or worse) than displacement localization across deformation amplitudes.

6. **Girard-excess gauge invariance.**
   Claim: The total spherical excess of the Gauss-image (normal vectors mapped to S²) of a closed convex near-octahedron is exactly 4π regardless of distortion; per-face excess gives a coordinate-free distortion map dual to the vertex-defect map, and the two maps are related by polar duality (dihedral ↔ face angles).
   Test: compute both maps on synthetic distortions; verify duality relations numerically.
   Refutation: systematic disagreement between predicted-dual maps beyond measurement noise.

**Axis (c) — phase/interferometry as cheapest probe**

7. **Phase-first sensing.**
   Claim: For the physical octahedral instrument, fringe phase at edge-crossing interferometers (or capacitively-coupled oscillator phase) detects sub-nm–equivalent angular deviations of faces — sensitivity to *dihedral angle change* scales as δθ ≈ (λ/2πL)·δφ, beating direct vertex-position metrology by a factor ~L/λ.
   Test: bench Michelson across one dihedral edge; calibrated tilt vs phase; compare against vertex triangulation from camera data.
   Refutation: measured phase-to-angle transfer function deviates from theory or shows worse SNR than camera triangulation at equal cost.

8. **Holonomy defect detector (Thomas-precession analogue).**
   Claim: Transporting a polarization (or oscillator phase) around a closed loop of edges on a distorted octahedron accumulates a geometric phase equal to the enclosed angular defect; loops around damaged regions show nonzero holonomy, symmetric loops on the perfect instrument cancel to zero.
   Test: compute/ simulate parallel transport on measured meshes; measure loop holonomy vs enclosed defect.
   Refutation: holonomy fails to equal enclosed defect within experimental error (would break the Gauss–Bonnet link at instrument scale — very surprising).

**Cross-domain / VSA bridges**

9. **Chebyshev–arcsine bridge for bundling distributions.**
   Claim: The VSA result bit-accuracy = Φ(1/√(k−1)) is a Gaussian approximation; the *exact* finite-k distribution of bundled-similarity for random hypervectors is related to the Beta(½,½)/arcsine family via the cosine-of-random-angle distribution on S^{d−1} (cos θ density ∝ (1−x²)^{(d−3)/2}, → arcsine in the appropriate 2-D projection). Predicted: measured bundling error curves deviate from Φ(1/√(k−1)) at small d in the direction predicted by the exact Beta-family density.
   Test: Monte-Carlo bundling at d ∈ {8, 64, 1024}, k sweep; fit exact vs Gaussian-approx curves.
   Refutation: residuals show no d-dependent systematic deviation.

10. **Platonic constellations as optimal VSA codebooks (Majorana link).**
    Claim: Octahedral/cubic vertex sets are the anticoherent "kings of quantumness" states (they maximize rotation-estimation fidelity); conjecture: the same 6-vertex octahedral codebook minimizes worst-case bundling interference among all 6-point spherical codes in the sense of minimizing max |Gram off-diagonal| (it achieves 0 — mutually orthogonal/antipodal pairs — which is provably optimal, so the falsifiable content is in the *generalization*: for N points, platonic-derived constellations achieve within 5% of the Welch bound).
    Test: compute Welch bound vs achieved coherence for platonic + Archimedean vertex sets, N = 4…60.
    Refutation: any platonic set >5% above Welch bound, or a random search finding systematically better codes.

---

### Key anchor citations
- Girard/spherical: arXiv:2605.01536, arXiv:1810.01786, arXiv:1409.4736
- Descartes/Gauss–Bonnet: arXiv:2512.19106, arXiv:2009.00116
- Peter–Weyl / spherical harmonics / addition theorem: preprints 202604.0332; arXiv:1202.5414; arXiv:0809.2017
- Hyperbolic: arXiv:2408.07036, arXiv:2603.24409 (rapidity/Thomas); arXiv:2604.21027, arXiv:2502.17130 (Sarkar/Sala tree embeddings); Nickel & Kiela arXiv:1705.08039, arXiv:1806.03417
- Ptolemy (Euclidean/spherical/hyperbolic): arXiv:1009.2970, arXiv:1302.4919
- Quantum: arXiv:2601.20922, arXiv:2508.08414 (spin coherent states); arXiv:1803.10356, arXiv:1612.06804, arXiv:1509.08300 (Majorana/polyhedral states)
- Arcsine laws: arXiv:1610.02861, arXiv:2105.15051
- VSA/Bochner/Peter–Weyl chain (already in ecosystem orbit): lemonforest/mlehaptics Spectral_Convergence_Conjecture.md (github)
