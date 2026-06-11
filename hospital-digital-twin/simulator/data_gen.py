# simulator/data_gen.py
import numpy as np
import pandas as pd
import yaml
from pathlib import Path

class SyntheticGenerator:
    def __init__(self, params_path="simulator/params.yaml", seed=42):
        self.params = yaml.safe_load(Path(params_path).read_text())
        self.rng = np.random.default_rng(seed or self.params.get("seed", 42))

    def hourly_lambda(self, dept, hour):
        p = self.params["departments"][dept]
        base = p["base_lambda"]
        amp = p["diurnal_amp"]
        # diurnal pattern: peak at 15:00 local
        phase = np.cos((hour - 15) / 24 * 2 * np.pi)
        lam = base * (1 + amp * phase)
        return max(0.01, lam)

    def sample_arrivals(self, dept, hour, surge=False):
        lam = self.hourly_lambda(dept, hour)
        if surge:
            lam *= self.params["surge"]["multiplier"]
        return self.rng.poisson(lam)

    def sample_severity(self, dept, n):
        probs = self.params["departments"][dept]["severity_probs"]
        keys = list(probs.keys())
        pvals = [probs[k] for k in keys]
        return self.rng.choice(keys, size=n, p=pvals)

    def sample_los_hours(self, dept, severities):
        los_params = self.params["departments"][dept]["los"]
        # lognormal around mean with moderate sigma
        out = []
        for s in severities:
            mean = los_params[s]
            sigma = 0.6
            # convert mean to lognormal mu/sigma
            mu = np.log(mean) - 0.5 * sigma**2
            val = self.rng.lognormal(mu, sigma)
            out.append(max(0.5, val))
        return np.array(out)

    def sample_med_demand(self, severities):
        # simple mapping: low->low meds, high->high meds
        mapping = {"low": (0,1), "medium": (1,3), "high": (3,8)}
        meds = [self.rng.integers(*mapping[s]) for s in severities]
        return np.array(meds)
