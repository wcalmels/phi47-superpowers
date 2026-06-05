# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
from __future__ import annotations
import numpy as np
from scipy import linalg


class PhiCalculator:
    """Calculates Phi for a connectivity matrix using spectral approximation (IIT 4.0).

    Example::

        calc = PhiCalculator()
        import numpy as np
        phi, meta = calc.calculate(np.random.rand(5, 5))
        print(phi)
    """

    def calculate(self, connectivity: np.ndarray, method: str = "spectral") -> tuple:
        """Calculate Phi.

        Args:
            connectivity: Square NxN float matrix.
            method: 'spectral' (fast, O(n^3)) or 'exact' (n<=8 only).

        Returns:
            Tuple of (phi: float, metadata: dict).
        """
        if connectivity.ndim != 2 or connectivity.shape[0] != connectivity.shape[1]:
            raise ValueError(f"Expected square matrix, got {connectivity.shape}")
        m = (connectivity + connectivity.T) / 2.0
        m = np.nan_to_num(m, nan=0.0)
        if method == "exact" and m.shape[0] <= 8:
            return self._exact(m)
        return self._spectral(m)

    def _spectral(self, m: np.ndarray) -> tuple:
        cov  = m @ m.T
        eigv = linalg.eigvalsh(cov)
        eigv = eigv[eigv > 1e-10]
        if not len(eigv):
            return 0.0, {"method": "spectral", "phi": 0.0}
        eigv /= eigv.sum()
        h   = float(-np.sum(eigv * np.log2(eigv + 1e-12)))
        k   = float(np.mean(np.abs(m)))
        phi = h * (1.0 - np.exp(-k))
        return float(phi), {"method": "spectral", "phi": phi,
                            "total_information": h, "integration_factor": 1 - np.exp(-k)}

    def _exact(self, m: np.ndarray) -> tuple:
        from itertools import combinations
        n       = m.shape[0]
        all_idx = list(range(n))
        min_phi = float("inf")
        mip     = None
        for k in range(1, n // 2 + 1):
            for pa in combinations(all_idx, k):
                pa = list(pa)
                pb = [i for i in all_idx if i not in pa]
                mi = max(0.0,
                         np.linalg.norm(m[np.ix_(pa, pa)], "fro")
                         + np.linalg.norm(m[np.ix_(pb, pb)], "fro")
                         - np.linalg.norm(m, "fro"))
                if mi < min_phi:
                    min_phi, mip = mi, (pa, pb)
        phi = float(min_phi) if min_phi != float("inf") else 0.0
        return phi, {"method": "exact", "phi": phi, "mip": mip}
