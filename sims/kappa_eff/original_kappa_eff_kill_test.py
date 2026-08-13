# C6 mini: kappa_eff leading-indicator kill-criteria test (GM claim, torch, CPU).
# Claim under test: along a weight-perturbation ray theta + alpha*v, the effective
# curvature kappa_eff = |v^T H v| / v^T v (finite-difference HVP, eps=1e-4, GM's own
# convention) spikes BEFORE held-out accuracy collapses. Kill criteria:
#   K1: kappa_eff shows no peak anywhere before the accuracy-drop point, OR
#   K2: kappa_eff peak occurs at/after accuracy has already dropped > 5 points.
import torch, torch.nn as nn
torch.manual_seed(0)

# --- data: noisy 2D moons-ish, fixed ---
n = 2000
x1 = torch.rand(n)*3 - 1.5
y = (torch.sin(2.5*x1) + 0.3*torch.randn(n) > 0).float()
X = torch.stack([x1, torch.rand(n)*3-1.5], 1)
Xtr, Xte, ytr, yte = X[:1500], X[1500:], y[:1500], y[1500:]

net = nn.Sequential(nn.Linear(2, 32), nn.Tanh(), nn.Linear(32, 32), nn.Tanh(), nn.Linear(32, 2))
opt = torch.optim.Adam(net.parameters(), lr=3e-3)
for ep in range(200):
    opt.zero_grad()
    nn.functional.cross_entropy(net(Xtr), ytr.long()).backward()
    opt.step()

theta0 = torch.cat([p.detach().flatten() for p in net.parameters()])
loss_fn = lambda: nn.functional.cross_entropy(net(Xtr), ytr.long())

def set_theta(t):
    i = 0
    with torch.no_grad():
        for p in net.parameters():
            k = p.numel(); p.copy_(t[i:i+k].view(p.shape)); i += k

def acc():
    with torch.no_grad():
        return (net(Xte).argmax(1) == yte.long()).float().mean().item()

set_theta(theta0)
g = torch.cat([x.flatten() for x in torch.autograd.grad(loss_fn(), list(net.parameters()))]).detach()
v = g/g.norm()   # GM energy_sweep convention: ascent ray, not random direction
eps = 1e-4

def kappa_eff(t):
    set_theta(t + eps*v); g1 = torch.autograd.grad(loss_fn(), list(net.parameters()), create_graph=False)
    g1 = torch.cat([g.flatten() for g in g1]).detach()
    set_theta(t - eps*v); g2 = torch.cat([g.flatten() for g in torch.autograd.grad(loss_fn(), list(net.parameters()))]).detach()
    set_theta(t)
    hvp = (g1 - g2)/(2*eps)
    return abs((v*hvp).sum().item())

base_acc = acc()
print(f"baseline acc {base_acc:.3f}")
print("alpha   acc    dAcc    kappa_eff")
rows = []
for alpha in [0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0]:
    k = kappa_eff(theta0 + alpha*v)
    a = acc()
    rows.append((alpha, a, a - base_acc, k))
    print(f"{alpha:5.3f}  {a:.3f}  {a-base_acc:+.3f}   {k:10.3f}")

# verdict
kappas = [r[3] for r in rows]; alphas = [r[0] for r in rows]
peak_a = alphas[kappas.index(max(kappas))]
drop_a = next((r[0] for r in rows if r[2] < -0.05), None)
print(f"\nkappa_eff peak at alpha={peak_a}; accuracy -5pt at alpha={drop_a}")
if drop_a is None: print("K1-K2 inconclusive: no accuracy collapse in range")
elif max(kappas[1:]) < 1.2*kappas[0] and peak_a == 0: print("K1 FIRED: no kappa peak before collapse - claim REFUTED on this ray")
elif peak_a >= drop_a: print("K2 FIRED: kappa peak not leading - claim REFUTED on this ray")
else: print(f"SUPPORTED on this ray: kappa_eff leads accuracy drop by {drop_a-peak_a:.3f} alpha units")
