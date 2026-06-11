# simulator/data_gen.py
import numpy as np
import pandas as pd
import yaml
from pathlib import Path
import logging

logger = logging.getLogger("simulator.data_gen")
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [data_gen] %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

class SyntheticGenerator:
    def __init__(self, params_path="simulator/params.yaml", seed=None):
        self.params_path = Path(params_path)
        if not self.params_path.exists():
            raise FileNotFoundError(f"params file not found: {self.params_path}")
        self.params = yaml.safe_load(self.params_path.read_text())
        self._validate_params()
        seed = seed if seed is not None else self.params.get("seed", 42)
        self.rng = np.random.default_rng(seed)

    def _validate_params(self):
        # Basic structure checks and normalization of severity_probs
        depts = self.params.get("departments", {})
        if not depts:
            raise ValueError("No departments defined in params.yaml")
        for dept, cfg in depts.items():
            sp = cfg.get("severity_probs")
            if not isinstance(sp, dict):
                raise ValueError(f"severity_probs for {dept} must be a mapping")
            # convert to floats and check
            cleaned = {}
            for k, v in sp.items():
                try:
                    cleaned[k] = float(v)
                except Exception:
                    logger.warning("Invalid severity_probs value for %s.%s: %r; treating as 0", dept, k, v)
                    cleaned[k] = 0.0
            total = sum(cleaned.values())
            if total <= 0 or not np.isfinite(total):
                logger.warning("Severity probs for %s sum to %s; replacing with uniform distribution", dept, total)
                n = max(1, len(cleaned))
                uniform = {k: 1.0/n for k in cleaned.keys()}
                self.params["departments"][dept]["severity_probs"] = uniform
            else:
                # normalize to sum=1.0
                norm = {k: float(v)/total for k, v in cleaned.items()}
                self.params["departments"][dept]["severity_probs"] = norm
        # staff and surge defaults
        self.params.setdefault("staff", {"nurses_per_patient": {"ED":0.2, "ICU":1.0, "Ward":0.1}})
        self.params.setdefault("surge", {"prob_per_day":0.05, "multiplier":2.5})

    def hourly_lambda(self, dept, hour):
        p = self.params["departments"][dept]
        base = float(p.get("base_lambda", 1.0))
        amp = float(p.get("diurnal_amp", 0.0))
        # diurnal pattern: peak at 15:00
        phase = np.cos((hour - 15) / 24 * 2 * np.pi)
        lam = base * (1 + amp * phase)
        return max(0.01, float(lam))

    def sample_arrivals(self, dept, hour, surge=False):
        lam = self.hourly_lambda(dept, hour)
        if surge:
            lam *= float(self.params["surge"].get("multiplier", 2.5))
        # Poisson with RNG
        return int(self.rng.poisson(lam))

    def sample_severity(self, dept, n):
        probs = self.params["departments"][dept]["severity_probs"]
        keys = list(probs.keys())
        pvals = np.array([float(probs[k]) for k in keys], dtype=float)
        # safety checks
        if np.any(~np.isfinite(pvals)) or pvals.sum() <= 0:
            logger.warning("Invalid severity probs for %s: %s; using uniform", dept, pvals)
            pvals = np.ones_like(pvals) / len(pvals)
        else:
            # normalize to sum 1 (protect against tiny floating error)
            pvals = pvals / pvals.sum()
        # final guard: replace NaN with uniform
        if np.any(np.isnan(pvals)):
            logger.warning("NaN detected in normalized probs for %s; falling back to uniform", dept)
            pvals = np.ones(len(keys)) / len(keys)
        # sample
        try:
            return self.rng.choice(keys, size=n, p=pvals)
        except Exception as e:
            logger.error("Sampling severity failed for dept=%s n=%s pvals=%s error=%s", dept, n, pvals, e)
            # fallback: uniform sampling
            return self.rng.choice(keys, size=n)

    def sample_los_hours(self, dept, severities):
        los_params = self.params["departments"][dept].get("los", {})
        out = []
        for s in severities:
            mean = float(los_params.get(s, 24.0))
            sigma = 0.6
            mu = np.log(max(0.1, mean)) - 0.5 * sigma**2
            val = self.rng.lognormal(mu, sigma)
            out.append(max(0.5, val))
        return np.array(out)

    def sample_med_demand(self, severities):
        mapping = {"low": (0,1), "medium": (1,3), "high": (3,8)}
        meds = []
        for s in severities:
            lo, hi = mapping.get(s, (0,1))
            meds.append(int(self.rng.integers(lo, hi+1)))
        return np.array(meds)
