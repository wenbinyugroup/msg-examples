"""Fang et al. (2019) energy-ratio-based measure of elastic anisotropy.

Core of r1_anisotropy_measure/scripts/energy_ratio_based_measure.py. Solved by the
reduced form

    A = max_Q  lambda_max(C_k, R(Q)^T C_k R(Q)) - 1

where Q runs over all 3D rotations, R(Q) is its 6x6 Kelvin rotation and lambda_max is
the largest generalized eigenvalue of the pencil. A is zero iff C is isotropic,
dimensionless and invariant under rotation and scaling of C.

Engineering Voigt order: (11, 22, 33, 23, 13, 12).
"""

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation

VOIGT = [(0, 0), (1, 1), (2, 2), (1, 2), (0, 2), (0, 1)]
_W = np.array([1, 1, 1, np.sqrt(2), np.sqrt(2), np.sqrt(2)])

# Kelvin basis of symmetric second-order tensors: orthonormal under A:B, which makes
# R(Q) orthogonal (the engineering Voigt rotations are not).
KELVIN_BASIS = []
for _i, _j in VOIGT:
    _E = np.zeros((3, 3))
    _E[_i, _j] = _E[_j, _i] = 1.0 if _i == _j else 1 / np.sqrt(2)
    KELVIN_BASIS.append(_E)


def kelvin_rotation(Q):
    """6x6 Kelvin rotation of a 3x3 rotation Q."""
    R = np.array([[np.tensordot(F, Q @ E @ Q.T) for E in KELVIN_BASIS] for F in KELVIN_BASIS])
    assert np.abs(R @ R.T - np.eye(6)).max() < 1e-12
    return R


def so3_grid(n):
    """n near-uniform orientations on SO(3) (super-Fibonacci, Alexa 2022)."""
    phi = np.sqrt(2.0)
    psi = 1.533751168755204288118041  # real root of psi**4 = psi + 4
    i = np.arange(n) + 0.5
    s = i / n
    r, r_c = np.sqrt(s), np.sqrt(1.0 - s)
    a, b = 2.0 * np.pi * i / phi, 2.0 * np.pi * i / psi
    quat = np.stack([r * np.sin(a), r * np.cos(a), r_c * np.sin(b), r_c * np.cos(b)], axis=1)
    return Rotation.from_quat(quat).as_matrix()


def _energy_ratios(C_kelvin, Q):
    """Max energy ratio at orientation Q, and the one at Q^-1 (reciprocal spectrum, free)."""
    R = kelvin_rotation(Q)
    eigenvalues = eigh(C_kelvin, R.T @ C_kelvin @ R, eigvals_only=True)
    return eigenvalues[-1], 1.0 / eigenvalues[0]


def energy_ratio_based_measure(C_voigt, n_coarse=3000, n_refine=20):
    """Return A_energy_ratio for a 6x6 Voigt stiffness matrix."""
    C = np.asarray(C_voigt, dtype=float)
    if C.shape != (6, 6) or np.abs(C - C.T).max() > 1e-10 * np.abs(C).max():
        raise ValueError("expected a symmetric 6x6 stiffness matrix")
    if np.linalg.eigvalsh(C).min() <= 0:
        raise ValueError("stiffness matrix is not positive definite")
    C_kelvin = C * np.outer(_W, _W)
    C_kelvin /= np.linalg.eigvalsh(C_kelvin).max()  # A is scale invariant; helps conditioning

    # Coarse scan locates the basins; Nelder-Mead on the rotation vector supplies the accuracy.
    grid = so3_grid(n_coarse)
    coarse = np.array([max(_energy_ratios(C_kelvin, Q)) for Q in grid])
    best = coarse.max()
    for index in np.argsort(coarse)[-n_refine:]:
        result = minimize(
            lambda v: -np.log(max(_energy_ratios(C_kelvin, Rotation.from_rotvec(v).as_matrix()))),
            Rotation.from_matrix(grid[index]).as_rotvec(), method="Nelder-Mead",
            options=dict(xatol=1e-11, fatol=1e-13, maxiter=5000),
        )
        best = max(best, np.exp(-result.fun))
    return best - 1.0


def _upper(values):
    """Symmetric 6x6 from its row-wise upper triangle."""
    c = np.zeros((6, 6))
    c[np.triu_indices(6)] = values
    return c + np.triu(c, 1).T


if __name__ == "__main__":
    E, nu = 70e9, 0.33
    lam, mu = E * nu / ((1 + nu) * (1 - 2 * nu)), E / (2 * (1 + nu))
    C_iso = np.diag([2 * mu] * 3 + [mu] * 3) + lam * np.pad(np.ones((3, 3)), (0, 3))
    assert abs(energy_ratio_based_measure(C_iso)) < 1e-9

    # Fang et al. 2019 supplemental C_random1, reference A = 2.2227
    C_random1 = _upper([7.6962, -0.6707, 0.3231, -0.0073, -0.8072, 0.6634,
                        5.6520, 0.3078, -0.0384, 1.2073, 0.5394,
                        5.9241, 0.1966, 0.1132, 0.2033,
                        6.5688, 0.2599, 0.1318,
                        7.5491, -1.0035,
                        6.6778])
    A = energy_ratio_based_measure(C_random1)
    assert abs(A - 2.2227) < 1e-3, A
    print(f"self-checks passed: isotropic -> 0, Fang C_random1 -> {A:.4f}")
