#!/usr/bin/env python3
"""Helper: localizar articulos en corpus y fuente oficial de LEY-142."""
import re, json, unicodedata

import re, json, unicodedata, os
os.chdir(os.path.expanduser('~/Documentos/DESARROLLO/SINORA/ORO-OS/ORO-OS/Norma'))
CORPUS = 'normas_procesar/LEY-142-1994.md'
FUENTE = 'sistema/verificacion/fuentes/LEY-142-1994.oficial.txt'

def norm(s):
    return unicodedata.normalize('NFC', s)

def load_corpus():
    return norm(open(CORPUS, encoding='utf-8').read())

def load_fuente():
    return norm(open(FUENTE, encoding='utf-8').read())

# ---- corpus: **ARTÍCULO 3. Título...** o ## ARTÍCULO
CORP_RE = re.compile(r'\*\*ARTÍCULO\s+(\d{1,3})[º°o]*\.\s', re.U)

def corpus_articles():
    txt = load_corpus()
    ms = list(CORP_RE.finditer(txt))
    arts = {}
    for i, m in enumerate(ms):
        end = ms[i+1].start() if i+1 < len(ms) else len(txt)
        arts[int(m.group(1))] = (m.start(), end, txt[m.start():end])
    return arts

# ---- fuente: ARTÍCULO 3o. / ARTÍCULO 40. / ARTÍCULO NUM
FUENTE_RE = re.compile(r'ARTÍCULO\s+(\d{1,3})\s*(?:o\.|º\.|°\.|\.)', re.U)

def fuente_articles():
    txt = load_fuente()
    ms = list(FUENTE_RE.finditer(txt))
    arts = {}
    for i, m in enumerate(ms):
        end = ms[i+1].start() if i+1 < len(ms) else len(txt)
        arts[int(m.group(1))] = (m.start(), end, txt[m.start():end])
    return arts

def low(s):
    return ''.join(c for c in unicodedata.normalize('NFKD', s.lower()) if unicodedata.category(c) != 'Mn')

def show_corpus(n, needle=None, w=200):
    arts = corpus_articles()
    if n not in arts:
        print(f'corpus art {n}: NO ENCONTRADO')
        return ''
    seg = arts[n][2]
    if needle:
        i = low(seg).find(low(needle))
        if i < 0:
            print(f'corpus art {n}: needle "{needle}" no hallado')
            return seg
        a, b = max(0, i-w), min(len(seg), i+w)
        print(f'--- corpus art {n} (ctx) ---')
        print(seg[a:b].replace('\n', ' '))
    else:
        print(f'--- corpus art {n} ---')
        print(seg[:w*2].replace('\n', ' '))
    return seg

def show_fuente(n, needle=None, w=200):
    arts = fuente_articles()
    if n not in arts:
        print(f'fuente art {n}: NO ENCONTRADO')
        return ''
    seg = arts[n][2]
    if needle:
        i = low(seg).find(low(needle))
        if i < 0:
            print(f'fuente art {n}: needle "{needle}" no hallado')
            return seg
        a, b = max(0, i-w), min(len(seg), i+w)
        print(f'--- fuente art {n} (ctx) ---')
        print(seg[a:b].replace('\n', ' '))
    else:
        print(f'--- fuente art {n} ---')
        print(seg[:w*2].replace('\n', ' '))
    return seg

if __name__ == '__main__':
    import sys
    ca, fa = corpus_articles(), fuente_articles()
    print('corpus articulos:', sorted(ca)[:20], '... total', len(ca))
    print('fuente articulos:', sorted(fa)[:20], '... total', len(fa))
    d = json.load(open('sistema/verificacion/informes/analisis-ley142.json'))
    sos = [int(x['articulo']) for x in d['buckets']['contenido_real']]
    print('sospechosos:', sos)
    print('en corpus falta:', [n for n in sos if n not in ca])
    print('en fuente falta:', [n for n in sos if n not in fa])
