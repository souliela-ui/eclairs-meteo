#!/usr/bin/env python3
"""Relais « éclairs » pour l'app Météo.

Télécharge les éclairs détectés par l'imageur de foudre du satellite Meteosat Third Generation
(EUMETSAT, produit LI Level 2 « Lightning Flashes », collection EO:EUM:DAT:0691) sur les
dernières heures, ne garde que ceux de la zone choisie et publie un petit fichier JSON :

    {"generated": "2026-09-26T21:40:00Z",
     "source": "EUMETSAT MTG LI L2 Lightning Flashes",
     "bbox": [lat_min, lon_min, lat_max, lon_max],
     "flashes": [[heure_unix, latitude, longitude], ...]}

Identifiants EUMETSAT (gratuits) : variables d'environnement EUMETSAT_CONSUMER_KEY et
EUMETSAT_CONSUMER_SECRET (clés « Consumer key / secret » du compte EUMETSAT).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import tempfile

import numpy as np
import xarray as xr

COLLECTION = "EO:EUM:DAT:0691"          # LI Lightning Flashes - MTG - 0 degree
EPOCH_2000 = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)
# France métropolitaine + marges (lat_min, lon_min, lat_max, lon_max)
DEFAULT_BBOX = (41.0, -5.5, 51.5, 10.0)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--hours", type=float, default=3.0, help="profondeur de l'historique (heures)")
    parser.add_argument("--bbox", type=float, nargs=4, metavar=("LAT_MIN", "LON_MIN", "LAT_MAX", "LON_MAX"),
                        default=DEFAULT_BBOX, help="zone conservée")
    parser.add_argument("--out", default="lightning.json", help="fichier JSON produit")
    return parser.parse_args()


def flashes_from_netcdf(path: str, bbox: tuple[float, float, float, float]) -> list[list[float]]:
    """Extrait [heure_unix, lat, lon] des éclairs d'un fichier « BODY » LI-2-LFL situés dans la zone."""
    lat_min, lon_min, lat_max, lon_max = bbox
    # decode_times=False : flash_time reste en secondes depuis le 2000-01-01 (convention LI L2).
    with xr.open_dataset(path, decode_times=False, mask_and_scale=True) as ds:
        if not {"flash_time", "latitude", "longitude"} <= set(ds.variables):
            return []
        seconds = np.asarray(ds["flash_time"].values, dtype="float64").ravel()
        lat = np.asarray(ds["latitude"].values, dtype="float64").ravel()
        lon = np.asarray(ds["longitude"].values, dtype="float64").ravel()

    valid = np.isfinite(seconds) & np.isfinite(lat) & np.isfinite(lon)
    valid &= (lat >= lat_min) & (lat <= lat_max) & (lon >= lon_min) & (lon <= lon_max)
    unix = seconds[valid] + EPOCH_2000.timestamp()
    return [[round(float(t), 1), round(float(a), 4), round(float(o), 4)]
            for t, a, o in zip(unix, lat[valid], lon[valid])]


def download_flashes(hours: float, bbox: tuple[float, float, float, float]) -> list[list[float]]:
    import eumdac  # importé ici : le reste du script reste testable sans identifiants

    key = os.environ.get("EUMETSAT_CONSUMER_KEY")
    secret = os.environ.get("EUMETSAT_CONSUMER_SECRET")
    if not key or not secret:
        sys.exit("Identifiants manquants : EUMETSAT_CONSUMER_KEY / EUMETSAT_CONSUMER_SECRET")

    token = eumdac.AccessToken((key, secret))
    collection = eumdac.DataStore(token).get_collection(COLLECTION)
    end = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    start = end - dt.timedelta(hours=hours)
    products = list(collection.search(dtstart=start, dtend=end))
    print(f"{len(products)} produit(s) LI-2-LFL entre {start:%H:%M} et {end:%H:%M} UTC")

    flashes: list[list[float]] = []
    with tempfile.TemporaryDirectory() as workdir:
        for product in products:
            # Seuls les morceaux « BODY » contiennent les éclairs (le « TRAIL » décrit le produit).
            entries = [e for e in product.entries if e.endswith(".nc") and "BODY" in e]
            for entry in entries:
                path = os.path.join(workdir, os.path.basename(entry))
                try:
                    with product.open(entry=entry) as source, open(path, "wb") as target:
                        target.write(source.read())
                    flashes.extend(flashes_from_netcdf(path, bbox))
                except Exception as error:  # un morceau illisible ne doit pas bloquer les autres
                    print(f"  ignoré {entry} : {error}")
                finally:
                    if os.path.exists(path):
                        os.remove(path)
    return flashes


def main() -> None:
    args = parse_args()
    bbox = tuple(args.bbox)
    flashes = sorted(download_flashes(args.hours, bbox))
    payload = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "EUMETSAT MTG LI L2 Lightning Flashes",
        "bbox": list(bbox),
        "flashes": flashes,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, separators=(",", ":"))
    print(f"{len(flashes)} éclair(s) écrit(s) dans {args.out}")


if __name__ == "__main__":
    main()
