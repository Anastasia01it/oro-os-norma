#!/usr/bin/env python3
"""Verificaciones compartidas del índice y el corpus (usadas por build y checks)."""
from __future__ import annotations

import hashlib
import sqlite3


def coverage_report(con: sqlite3.Connection, disk_names: set, manifest_names: set) -> dict:
    db_names = {r[0] for r in con.execute("SELECT filename FROM docs")}
    return {
        "db": db_names,
        "disk": disk_names,
        "manifest": manifest_names,
        "faltan_en_db": sorted(disk_names - db_names),
        "extras_en_db": sorted(db_names - disk_names),
        "faltan_en_manifest": sorted(disk_names - manifest_names),
        "extras_en_manifest": sorted(manifest_names - disk_names),
    }


def verify_lossless(con: sqlite3.Connection) -> list:
    """Reconstruye cada archivo desde sus chunks y compara SHA-256.

    Usa la codificación registrada en docs (utf-8 / latin-1) para que la
    reconstrucción sea byte-por-byte igual al original.
    Devuelve la lista de archivos cuya reconstrucción NO coincide (debe ser []).
    """
    bad = []
    rows = con.execute(
        "SELECT file_id, filename, sha256, encoding FROM docs ORDER BY file_id"
    ).fetchall()
    for file_id, filename, sha, encoding in rows:
        text = "".join(
            t for (t,) in con.execute(
                "SELECT text FROM chunks WHERE file_id = ? ORDER BY chunk_no", (file_id,)
            )
        )
        digest = hashlib.sha256(text.encode(encoding)).hexdigest()
        if digest != sha:
            bad.append(filename)
    return bad
