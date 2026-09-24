#!/usr/bin/env python3
"""Construye sistema/data/corpus.index.sqlite (SQLite FTS5) desde el corpus verificado.

Pre-condición (fail-closed): todo archivo del corpus debe coincidir con el
manifiesto (SHA-256). Si hay agregados, eliminados o modificados, NO se indexa.

Garantías auto-verificadas al terminar:
1. Cobertura: el índice contiene exactamente los archivos del corpus.
2. Reconstrucción lossless: concatenar los chunks de un archivo reproduce
   byte-por-byte su contenido (igualdad de SHA-256).

Segmentación: por líneas de encabezado Markdown (# … ######). Un archivo sin
encabezados queda como un único chunk. El texto se almacena íntegro: el índice
sirve de respaldo verificable, no solo de búsqueda.
"""
import json
import re
import sqlite3
import sys

from corpus_config import DB_DIR, DB_PATH, MANIFEST_PATH, corpus_files, read_text_lossless, sha256_file
from corpus_verify import coverage_report, verify_lossless

SPLIT_RE = re.compile(r"(?m)^(#{1,6} .*?)$")


def split_chunks(text: str) -> list:
    """Segmenta por encabezados. ''.join(c['text'] for c in chunks) == texto original."""
    matches = list(SPLIT_RE.finditer(text))
    if not matches:
        return [{"heading": None, "text": text}]
    chunks = []
    if matches[0].start() > 0:
        chunks.append({"heading": None, "text": text[: matches[0].start()]})
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunks.append({"heading": m.group(1).strip(), "text": text[m.start():end]})
    return chunks


def check_manifest() -> dict:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    disk = {p.name: sha256_file(p) for p in corpus_files()}
    man = manifest["files"]
    added = sorted(set(disk) - set(man))
    removed = sorted(set(man) - set(disk))
    modified = sorted(n for n in set(disk) & set(man) if disk[n] != man[n]["sha256"])
    if added or removed or modified:
        print("ERROR: corpus divergente del manifiesto. No se indexa.")
        for tag, lst in (("AGREGADOS", added), ("ELIMINADOS", removed), ("MODIFICADOS", modified)):
            if lst:
                print(f"  {tag}: {lst}")
        sys.exit(1)
    return manifest


def build(manifest: dict) -> None:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = sqlite3.connect(DB_PATH)
    con.executescript(
        """
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE docs (
          file_id  INTEGER PRIMARY KEY,
          filename TEXT NOT NULL UNIQUE,
          sha256   TEXT NOT NULL,
          bytes    INTEGER NOT NULL,
          encoding TEXT NOT NULL
        );
        CREATE TABLE chunks (
          chunk_id INTEGER PRIMARY KEY,
          file_id  INTEGER NOT NULL REFERENCES docs(file_id),
          chunk_no INTEGER NOT NULL,
          heading  TEXT,
          text     TEXT NOT NULL
        );
        CREATE INDEX idx_chunks_file ON chunks(file_id, chunk_no);
        CREATE VIRTUAL TABLE chunks_fts USING fts5(text, heading, filename);
        """
    )
    total_chunks = 0
    for p in corpus_files():
        text, enc = read_text_lossless(p)
        chunks = split_chunks(text)
        cur = con.execute(
            "INSERT INTO docs (filename, sha256, bytes, encoding) VALUES (?, ?, ?, ?)",
            (p.name, sha256_file(p), p.stat().st_size, enc),
        )
        file_id = cur.lastrowid
        for no, ch in enumerate(chunks):
            con.execute(
                "INSERT INTO chunks (file_id, chunk_no, heading, text) VALUES (?, ?, ?, ?)",
                (file_id, no, ch["heading"], ch["text"]),
            )
            con.execute(
                "INSERT INTO chunks_fts (rowid, text, heading, filename) VALUES (?, ?, ?, ?)",
                (total_chunks + 1, ch["text"], ch["heading"] or "", p.name),
            )
            total_chunks += 1
    con.execute("INSERT INTO meta VALUES ('build_at', ?)", (__import__("corpus_config").iso_now(),))
    con.execute("INSERT INTO meta VALUES ('set_hash', ?)", (manifest["set_hash"],))
    con.commit()

    # Auto-verificación
    bad = verify_lossless(con)
    cov = coverage_report(con, {p.name for p in corpus_files()}, set(manifest["files"]))
    con.close()
    if bad:
        print(f"ERROR: reconstrucción lossless falló en {len(bad)} archivos: {bad[:5]}")
        sys.exit(1)
    if cov["faltan_en_db"] or cov["extras_en_db"]:
        print("ERROR: cobertura del índice incompleta.")
        sys.exit(1)
    print(f"OK | índice: {DB_PATH.name}")
    print(f"   docs: {manifest['file_count']} | chunks: {total_chunks} | reconstrucción: 0 fallos")


if __name__ == "__main__":
    build(check_manifest())
