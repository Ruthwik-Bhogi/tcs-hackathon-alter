# simulator/engine.py
import pandas as pd
import numpy as np
import time
import logging
from simulator.data_gen import SyntheticGenerator
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger("simulator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

class Patient:
    def __init__(self, id, dept, severity, arrival_time, los_hours, meds):
        self.id = id
        self.dept = dept
        self.severity = severity
        self.arrival_time = arrival_time
        self.discharge_time = arrival_time + timedelta(hours=float(los_hours))
        self.meds = meds

class Simulator:
    def __init__(self, start_time=None, seed=42, params_path="simulator/params.yaml"):
        self.gen = SyntheticGenerator(params_path=params_path, seed=seed)
        self.now = start_time or datetime.now().replace(minute=0, second=0, microsecond=0)
        self.patients = []
        self.next_id = 1
        self.history = []  # list of snapshots
        self.depts = list(self.gen.params["departments"].keys())

    def step_hour(self, hour_offset=0, inject_surge=False):
        t = self.now + timedelta(hours=hour_offset)
        hour = t.hour
        new_patients = []
        for dept in self.depts:
            arrivals = self.gen.sample_arrivals(dept, hour, surge=inject_surge)
            if arrivals <= 0:
                continue
            severities = self.gen.sample_severity(dept, arrivals)
            los = self.gen.sample_los_hours(dept, severities)
            meds = self.gen.sample_med_demand(severities)
            for s, l, m in zip(severities, los, meds):
                p = Patient(self.next_id, dept, s, t, l, m)
                self.patients.append(p)
                new_patients.append(p)
                self.next_id += 1
        # remove discharged
        before = len(self.patients)
        self.patients = [p for p in self.patients if p.discharge_time > t]
        after = len(self.patients)
        snapshot = self._snapshot(t, new_patients, before, after)
        self.history.append(snapshot)
        return snapshot

    def _snapshot(self, t, new_patients, before, after):
        counts = {d: 0 for d in self.depts}
        meds = {d: 0 for d in self.depts}
        staff_load = {d: 0.0 for d in self.depts}
        for p in self.patients:
            counts[p.dept] += 1
            meds[p.dept] += p.meds
        for d in self.depts:
            ratio = self.gen.params["staff"]["nurses_per_patient"].get(d, 0.2)
            staff_load[d] = counts[d] * ratio
        snap = {
            "time": t,
            "counts": counts,
            "meds": meds,
            "staff_load": staff_load,
            "new_arrivals": {d: sum(1 for p in new_patients if p.dept == d) for d in self.depts},
            "total_before": before,
            "total_after": after
        }
        logger.debug("Snapshot: %s", snap)
        return snap

    def run_hours(self, hours=24, surge_hours=None):
        # surge_hours: list of hour offsets to inject surge
        for h in range(hours):
            inject = (surge_hours and h in surge_hours)
            self.step_hour(hour_offset=h, inject_surge=inject)
        return pd.DataFrame([{
            "time": s["time"],
            **{f"{d}_count": s["counts"][d] for d in self.depts},
            **{f"{d}_meds": s["meds"][d] for d in self.depts},
            **{f"{d}_staff": s["staff_load"][d] for d in self.depts},
            "new_total": sum(s["new_arrivals"].values())
        } for s in self.history])
