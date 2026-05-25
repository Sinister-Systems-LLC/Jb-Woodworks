#!/usr/bin/env python3
"""hgly_corpus_seed.py - bootstrap the training corpus for Sinister Hieroglyphics.

Author: RKOJ-ELENO :: 2026-05-25

Purpose
=======
Phase 1.5 corpus seeder for the 4090 LoRA trainer
(automations/hgly_trainer.py). The trainer reads from
_shared-memory/hgly-corpus/ which is empty on bootstrap. This module
generates deterministic seed programs for the 64-glyph language defined in
projects/sinister-hieroglyphics/docs/GLYPH-SYNTAX.md (Phase 1).

Three layers:

  1. gen   -- local deterministic template generation (no swarm).
  2. fanout -- multi-agent parallel generation via sinister_swarm.fanout.
  3. ingest -- validate swarm-results JSON + drop .shp files into corpus.

Plus a `stats` subcommand for corpus coverage histograms.

Composes with:
  - automations/sinister_swarm.py (fanout)
  - automations/hgly_trainer.py (consumer of _shared-memory/hgly-corpus/)
  - projects/sinister-hieroglyphics/docs/GLYPH-SYNTAX.md (64-glyph spec)

Constraints (operator hard-canonical 2026-05-25):
  - Pure Python 3 (no .bat, no .ps1).
  - stdlib only (argparse + json + pathlib + ...; no requests / no click).
  - Every subcommand accepts --dry-run.
  - gen + ingest standalone; fanout is the multi-agent layer.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import pathlib
import random
import re
import sys
import uuid
from typing import Any, Iterable, Optional

# Reconfigure stdout/stderr to UTF-8 so glyph codepoints print on Windows cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# 64-glyph vocabulary (mirrors GLYPH-SYNTAX.md exactly)
# ---------------------------------------------------------------------------

# Each row: (idx, glyph, ascii_fallback, name, category)
GLYPHS: list[tuple[int, str, str, str, str]] = [
    # Category 1 - Bind / scope
    (1,  "\U00013080", "let", "bind-let",    "bind"),
    (2,  "\U000132AA", "cst", "bind-const",  "bind"),
    (3,  "\U0001318E", "fn",  "function",    "bind"),
    (4,  "\U0001339B", "ret", "return",      "bind"),
    (5,  "\U000133CF", "lam", "lambda",      "bind"),
    (6,  "\U0001337F", "as",  "alias",       "bind"),
    (7,  "\U0001309D", "{",   "scope-open",  "bind"),
    (8,  "\U0001309E", "}",   "scope-close", "bind"),
    # Category 2 - Control flow
    (9,  "\U00013079", "if",  "if",          "ctrl"),
    (10, "\U0001309C", "el",  "else",        "ctrl"),
    (11, "\U000130C0", "mch", "match",       "ctrl"),
    (12, "\U000130E2", "lp",  "loop",        "ctrl"),
    (13, "\U0001335E", "brk", "break",       "ctrl"),
    (14, "\U000133A1", "cnt", "continue",    "ctrl"),
    (15, "\U000133BC", "yld", "yield",       "ctrl"),
    (16, "\U00013283", "for", "for-range",   "ctrl"),
    # Category 3 - Arithmetic / logic
    (17, "➕",     "+",   "add",         "arith"),
    (18, "➖",     "-",   "sub",         "arith"),
    (19, "✖",     "*",   "mul",         "arith"),
    (20, "➗",     "/",   "div",         "arith"),
    (21, "☰",     "%",   "mod",         "arith"),
    (22, "∧",     "&&",  "and",         "arith"),
    (23, "∨",     "||",  "or",          "arith"),
    (24, "¬",     "!",   "not",         "arith"),
    # Category 4 - Memory
    (25, "\U00013274", "alc",  "alloc",   "mem"),
    (26, "\U00013261", "fre",  "free",    "mem"),
    (27, "\U000132BD", "mmp",  "mmap",    "mem"),
    (28, "\U000132F4", "umm",  "munmap",  "mem"),
    (29, "\U000132F9", "&",    "addr-of", "mem"),
    (30, "\U00013333", "*",    "deref",   "mem"),
    (31, "\U00013351", "cst!", "cast",    "mem"),
    (32, "\U0001339F", "siz",  "sizeof",  "mem"),
    # Category 5 - IO / syscall
    (33, "\U000130A7", "rd",  "read",    "io"),
    (34, "\U000130B8", "wr",  "write",   "io"),
    (35, "\U000130ED", "opn", "open",    "io"),
    (36, "\U0001311F", "cls", "close",   "io"),
    (37, "\U00013153", "sys", "syscall", "io"),
    (38, "\U00013171", "ioc", "ioctl",   "io"),
    (39, "\U00013184", "rcv", "recv",    "io"),
    (40, "\U00013191", "snd", "send",    "io"),
    # Category 6 - Concurrency
    (41, "\U00013197", "spn", "spawn",      "conc"),
    (42, "\U000131A3", "awt", "await",      "conc"),
    (43, "\U000131CB", "cs",  "chan-send",  "conc"),
    (44, "\U000131CC", "cr",  "chan-recv",  "conc"),
    (45, "\U000131D8", "lck", "mutex-lock", "conc"),
    (46, "\U000131DF", "ulk", "mutex-unlk", "conc"),
    (47, "\U0001320E", "atm", "atomic",     "conc"),
    (48, "\U00013216", "fnc", "fence",      "conc"),
    # Category 7 - Hardware
    (49, "\U00013217", "pin", "port-in",     "hw"),
    (50, "\U00013218", "pot", "port-out",    "hw"),
    (51, "\U00013250", "dma", "dma-start",   "hw"),
    (52, "\U00013254", "irq", "irq-mask",    "hw"),
    (53, "\U00013258", "gpu", "gpu-launch",  "hw"),
    (54, "\U0001325C", "cpf", "cpu-feature", "hw"),
    (55, "\U00013260", "prf", "perfctr-rd",  "hw"),
    (56, "\U000132B5", "msr", "msr-write",   "hw"),
    # Category 8 - Simulation
    (57, "\U000132FB", "snp", "snapshot",    "sim"),
    (58, "\U00013303", "stp", "step",        "sim"),
    (59, "\U00013319", "brn", "branch-sim",  "sim"),
    (60, "\U00013347", "mrg", "merge",       "sim"),
    (61, "\U00013371", "obs", "observe",     "sim"),
    (62, "\U000133A2", "prt", "perturb",     "sim"),
    (63, "\U000133C3", "rwd", "rewind",      "sim"),
    (64, "\U000133DB", "mat", "materialize", "sim"),
]

# Quick lookup tables
ASCII_BY_NAME: dict[str, str] = {row[3]: row[2] for row in GLYPHS}
GLYPH_BY_NAME: dict[str, str] = {row[3]: row[1] for row in GLYPHS}
# Also alias by ASCII fallback so templates can use `GLYPH_BY_NAME['let']`,
# `GLYPH_BY_NAME['for']`, etc. (canonical short names from the spec).
for _row in GLYPHS:
    GLYPH_BY_NAME.setdefault(_row[2], _row[1])
    ASCII_BY_NAME.setdefault(_row[2], _row[2])
ALL_GLYPH_CHARS: set[str] = {row[1] for row in GLYPHS}
# ASCII fallbacks as whole tokens (per GLYPH-SYNTAX.md disambiguation rule)
ALL_ASCII_TOKENS: set[str] = {row[2] for row in GLYPHS}


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _sanctum_root() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parent.parent


def _corpus_dir() -> pathlib.Path:
    return _sanctum_root() / "_shared-memory" / "hgly-corpus"


def _swarm_results_dir() -> pathlib.Path:
    return _sanctum_root() / "_shared-memory" / "inbox" / "swarm-results"


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


# ---------------------------------------------------------------------------
# Template library -- 20 deterministic .shp programs
# Each template returns (glyph_src, ascii_src, python_ref) for variant `v`.
# ---------------------------------------------------------------------------

def _tpl_hello_world(v: int) -> tuple[str, str, str]:
    msg = f"hello{v}\\n"
    g = (f"{GLYPH_BY_NAME['function']} main () {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['write']} 1 \"{msg}\" {len(msg)-1}\n"
         f"{GLYPH_BY_NAME['scope-close']}\nmain")
    a = (f"fn main () {{\n  wr 1 \"{msg}\" {len(msg)-1}\n}}\nmain")
    p = f"def main():\n    print(\"hello{v}\")\nmain()"
    return g, a, p


def _tpl_fizzbuzz(v: int) -> tuple[str, str, str]:
    n = 15 + v
    g = (f"{GLYPH_BY_NAME['function']} fb (n) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['for-range']} i 1 {GLYPH_BY_NAME['add']} n 1 "
         f"{GLYPH_BY_NAME['scope-open']}\n"
         f"    {GLYPH_BY_NAME['if']} (= {GLYPH_BY_NAME['mod']} i 15 0) "
         f"{GLYPH_BY_NAME['scope-open']} {GLYPH_BY_NAME['write']} 1 \"FizzBuzz\\n\" 9 "
         f"{GLYPH_BY_NAME['scope-close']}\n"
         f"    {GLYPH_BY_NAME['else']} {GLYPH_BY_NAME['if']} (= {GLYPH_BY_NAME['mod']} i 3 0) "
         f"{GLYPH_BY_NAME['scope-open']} {GLYPH_BY_NAME['write']} 1 \"Fizz\\n\" 5 "
         f"{GLYPH_BY_NAME['scope-close']}\n"
         f"    {GLYPH_BY_NAME['else']} {GLYPH_BY_NAME['if']} (= {GLYPH_BY_NAME['mod']} i 5 0) "
         f"{GLYPH_BY_NAME['scope-open']} {GLYPH_BY_NAME['write']} 1 \"Buzz\\n\" 5 "
         f"{GLYPH_BY_NAME['scope-close']}\n"
         f"    {GLYPH_BY_NAME['else']} {GLYPH_BY_NAME['scope-open']} "
         f"{GLYPH_BY_NAME['write']} 1 i 4 {GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['scope-close']}\n"
         f"{GLYPH_BY_NAME['scope-close']}\nfb {n}")
    a = (f"fn fb (n) {{\n  for i 1 + n 1 {{\n"
         f"    if (== % i 15 0) {{ wr 1 \"FizzBuzz\\n\" 9 }}\n"
         f"    el if (== % i 3 0) {{ wr 1 \"Fizz\\n\" 5 }}\n"
         f"    el if (== % i 5 0) {{ wr 1 \"Buzz\\n\" 5 }}\n"
         f"    el {{ wr 1 i 4 }}\n  }}\n}}\nfb {n}")
    p = (f"def fb(n):\n    for i in range(1, n+1):\n"
         f"        if i % 15 == 0: print('FizzBuzz')\n"
         f"        elif i % 3 == 0: print('Fizz')\n"
         f"        elif i % 5 == 0: print('Buzz')\n"
         f"        else: print(i)\nfb({n})")
    return g, a, p


def _tpl_fibonacci(v: int) -> tuple[str, str, str]:
    n = 10 + v
    g = (f"{GLYPH_BY_NAME['function']} fib (n) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['if']} (< n 2) {GLYPH_BY_NAME['scope-open']} "
         f"{GLYPH_BY_NAME['return']} n {GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['return']} {GLYPH_BY_NAME['add']} "
         f"(fib {GLYPH_BY_NAME['sub']} n 1) (fib {GLYPH_BY_NAME['sub']} n 2)\n"
         f"{GLYPH_BY_NAME['scope-close']}\nfib {n}")
    a = (f"fn fib (n) {{\n  if (< n 2) {{ ret n }}\n"
         f"  ret + (fib - n 1) (fib - n 2)\n}}\nfib {n}")
    p = (f"def fib(n):\n    if n < 2: return n\n"
         f"    return fib(n-1) + fib(n-2)\nfib({n})")
    return g, a, p


def _tpl_factorial(v: int) -> tuple[str, str, str]:
    n = 5 + v
    g = (f"{GLYPH_BY_NAME['function']} fact (n) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['let']} acc 1\n"
         f"  {GLYPH_BY_NAME['for-range']} i 1 {GLYPH_BY_NAME['add']} n 1 "
         f"{GLYPH_BY_NAME['scope-open']}\n"
         f"    {GLYPH_BY_NAME['let']} acc {GLYPH_BY_NAME['mul']} acc i\n"
         f"  {GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['return']} acc\n"
         f"{GLYPH_BY_NAME['scope-close']}\nfact {n}")
    a = (f"fn fact (n) {{\n  let acc 1\n"
         f"  for i 1 + n 1 {{ let acc * acc i }}\n"
         f"  ret acc\n}}\nfact {n}")
    p = (f"def fact(n):\n    acc = 1\n    for i in range(1, n+1):\n"
         f"        acc *= i\n    return acc\nprint(fact({n}))")
    return g, a, p


def _tpl_list_map(v: int) -> tuple[str, str, str]:
    n = 4 + v
    g = (f"{GLYPH_BY_NAME['function']} mp (xs) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['for-range']} i 0 {n} {GLYPH_BY_NAME['scope-open']}\n"
         f"    {GLYPH_BY_NAME['yield']} {GLYPH_BY_NAME['mul']} xs[i] 2\n"
         f"  {GLYPH_BY_NAME['scope-close']}\n"
         f"{GLYPH_BY_NAME['scope-close']}\nmp [1 2 3 {n}]")
    a = (f"fn mp (xs) {{\n  for i 0 {n} {{ yld * xs[i] 2 }}\n}}\nmp [1 2 3 {n}]")
    p = f"def mp(xs):\n    return [x*2 for x in xs]\nprint(mp([1,2,3,{n}]))"
    return g, a, p


def _tpl_list_filter(v: int) -> tuple[str, str, str]:
    n = 3 + v
    g = (f"{GLYPH_BY_NAME['function']} flt (xs) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['for-range']} i 0 {n} {GLYPH_BY_NAME['scope-open']}\n"
         f"    {GLYPH_BY_NAME['if']} (= {GLYPH_BY_NAME['mod']} xs[i] 2 0) "
         f"{GLYPH_BY_NAME['scope-open']} {GLYPH_BY_NAME['yield']} xs[i] "
         f"{GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['scope-close']}\n"
         f"{GLYPH_BY_NAME['scope-close']}\nflt [1 2 3 4 5]")
    a = (f"fn flt (xs) {{\n  for i 0 {n} {{\n"
         f"    if (== % xs[i] 2 0) {{ yld xs[i] }}\n  }}\n}}\nflt [1 2 3 4 5]")
    p = (f"def flt(xs):\n    return [x for x in xs if x%2==0]\n"
         f"print(flt([1,2,3,4,5]))")
    return g, a, p


def _tpl_list_reduce(v: int) -> tuple[str, str, str]:
    init = v
    g = (f"{GLYPH_BY_NAME['function']} red (xs) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['let']} acc {init}\n"
         f"  {GLYPH_BY_NAME['loop']} {GLYPH_BY_NAME['scope-open']}\n"
         f"    {GLYPH_BY_NAME['let']} acc {GLYPH_BY_NAME['add']} acc xs[0]\n"
         f"    {GLYPH_BY_NAME['break']}\n"
         f"  {GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['return']} acc\n"
         f"{GLYPH_BY_NAME['scope-close']}\nred [10 20 30]")
    a = (f"fn red (xs) {{\n  let acc {init}\n  lp {{\n"
         f"    let acc + acc xs[0]\n    brk\n  }}\n  ret acc\n}}\nred [10 20 30]")
    p = (f"def red(xs):\n    acc = {init}\n    for x in xs: acc += x\n"
         f"    return acc\nprint(red([10,20,30]))")
    return g, a, p


def _tpl_hashmap_iter(v: int) -> tuple[str, str, str]:
    n = 3 + v
    g = (f"{GLYPH_BY_NAME['function']} hi (m) {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['for-range']} i 0 {n} {GLYPH_BY_NAME['scope-open']}\n"
         f"    {GLYPH_BY_NAME['write']} 1 m[i] 8\n"
         f"  {GLYPH_BY_NAME['scope-close']}\n"
         f"{GLYPH_BY_NAME['scope-close']}\nhi map")
    a = (f"fn hi (m) {{\n  for i 0 {n} {{ wr 1 m[i] 8 }}\n}}\nhi map")
    p = (f"def hi(m):\n    for k,v in m.items(): print(k,v)\n"
         f"hi({{'a':1,'b':2}})")
    return g, a, p


def _tpl_file_read(v: int) -> tuple[str, str, str]:
    path = f"/tmp/in{v}.txt"
    g = (f"{GLYPH_BY_NAME['let']} fd ({GLYPH_BY_NAME['open']} \"{path}\" R)\n"
         f"{GLYPH_BY_NAME['let']} buf ({GLYPH_BY_NAME['alloc']} 1024)\n"
         f"{GLYPH_BY_NAME['read']} fd buf 1024\n"
         f"{GLYPH_BY_NAME['close']} fd\n"
         f"{GLYPH_BY_NAME['free']} buf")
    a = (f"let fd (opn \"{path}\" R)\nlet buf (alc 1024)\n"
         f"rd fd buf 1024\ncls fd\nfre buf")
    p = (f"with open('{path}') as f: data = f.read(1024)")
    return g, a, p


def _tpl_file_write(v: int) -> tuple[str, str, str]:
    path = f"/tmp/out{v}.txt"
    g = (f"{GLYPH_BY_NAME['let']} fd ({GLYPH_BY_NAME['open']} \"{path}\" W)\n"
         f"{GLYPH_BY_NAME['write']} fd \"data{v}\\n\" 6\n"
         f"{GLYPH_BY_NAME['close']} fd")
    a = (f"let fd (opn \"{path}\" W)\nwr fd \"data{v}\\n\" 6\ncls fd")
    p = (f"with open('{path}','w') as f: f.write('data{v}\\n')")
    return g, a, p


def _tpl_syscall_write(v: int) -> tuple[str, str, str]:
    n = 1 + v
    g = (f"{GLYPH_BY_NAME['syscall']} {n} [1 ptr {6+v}]")
    a = (f"sys {n} [1 ptr {6+v}]")
    p = (f"import os; os.write(1, b'msg{v}')")
    return g, a, p


def _tpl_channel_send_recv(v: int) -> tuple[str, str, str]:
    n = v
    g = (f"{GLYPH_BY_NAME['let']} ch (chan i64)\n"
         f"{GLYPH_BY_NAME['spawn']} ({GLYPH_BY_NAME['lambda']} () "
         f"{GLYPH_BY_NAME['scope-open']} {GLYPH_BY_NAME['chan-send']} ch {n} "
         f"{GLYPH_BY_NAME['scope-close']})\n"
         f"{GLYPH_BY_NAME['let']} v ({GLYPH_BY_NAME['chan-recv']} ch)\n"
         f"{GLYPH_BY_NAME['write']} 1 v 4")
    a = (f"let ch (chan i64)\nspn (lam () {{ cs ch {n} }})\n"
         f"let v (cr ch)\nwr 1 v 4")
    p = (f"import queue, threading\n"
         f"q = queue.Queue()\nthreading.Thread(target=lambda: q.put({n})).start()\n"
         f"print(q.get())")
    return g, a, p


def _tpl_mutex(v: int) -> tuple[str, str, str]:
    n = 100 + v
    g = (f"{GLYPH_BY_NAME['let']} m (mutex {n})\n"
         f"{GLYPH_BY_NAME['let']} p ({GLYPH_BY_NAME['mutex-lock']} m)\n"
         f"{GLYPH_BY_NAME['write']} 1 p 8\n"
         f"{GLYPH_BY_NAME['mutex-unlk']} m")
    a = (f"let m (mutex {n})\nlet p (lck m)\nwr 1 p 8\nulk m")
    p = (f"import threading\nm = threading.Lock()\n"
         f"with m: print({n})")
    return g, a, p


def _tpl_atomic_cas(v: int) -> tuple[str, str, str]:
    g = (f"{GLYPH_BY_NAME['let']} p ({GLYPH_BY_NAME['alloc']} 8)\n"
         f"{GLYPH_BY_NAME['atomic']} cas p {v}\n"
         f"{GLYPH_BY_NAME['free']} p")
    a = (f"let p (alc 8)\natm cas p {v}\nfre p")
    p = (f"import ctypes; v = ctypes.c_int({v}); _ = v.value")
    return g, a, p


def _tpl_gpu_matmul_stub(v: int) -> tuple[str, str, str]:
    n = 64 * (v + 1)
    g = (f"{GLYPH_BY_NAME['gpu-launch']} matmul [{n} {n}] [A B C]\n"
         f"{GLYPH_BY_NAME['await']} matmul")
    a = (f"gpu matmul [{n} {n}] [A B C]\nawt matmul")
    p = (f"import numpy as np\nA = np.zeros(({n},{n}))\n"
         f"B = np.zeros(({n},{n}))\nC = A @ B")
    return g, a, p


def _tpl_simulation_snapshot_step(v: int) -> tuple[str, str, str]:
    dt = 0.016 * (v + 1)
    g = (f"{GLYPH_BY_NAME['let']} w0 ({GLYPH_BY_NAME['snapshot']} world)\n"
         f"{GLYPH_BY_NAME['let']} w1 ({GLYPH_BY_NAME['step']} w0 {dt:.3f})\n"
         f"{GLYPH_BY_NAME['observe']} w1 pos")
    a = (f"let w0 (snp world)\nlet w1 (stp w0 {dt:.3f})\nobs w1 pos")
    p = (f"w0 = snapshot(world)\nw1 = step(w0, {dt:.3f})\nprint(observe(w1, 'pos'))")
    return g, a, p


def _tpl_loop_break_continue(v: int) -> tuple[str, str, str]:
    n = 5 + v
    g = (f"{GLYPH_BY_NAME['for-range']} i 0 {n} {GLYPH_BY_NAME['scope-open']}\n"
         f"  {GLYPH_BY_NAME['if']} (= {GLYPH_BY_NAME['mod']} i 2 0) "
         f"{GLYPH_BY_NAME['scope-open']} {GLYPH_BY_NAME['continue']} "
         f"{GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['if']} (> i 7) {GLYPH_BY_NAME['scope-open']} "
         f"{GLYPH_BY_NAME['break']} {GLYPH_BY_NAME['scope-close']}\n"
         f"  {GLYPH_BY_NAME['write']} 1 i 4\n"
         f"{GLYPH_BY_NAME['scope-close']}")
    a = (f"for i 0 {n} {{\n  if (== % i 2 0) {{ cnt }}\n"
         f"  if (> i 7) {{ brk }}\n  wr 1 i 4\n}}")
    p = (f"for i in range({n}):\n    if i%2==0: continue\n"
         f"    if i>7: break\n    print(i)")
    return g, a, p


def _tpl_match_pattern(v: int) -> tuple[str, str, str]:
    x = v
    g = (f"{GLYPH_BY_NAME['match']} {x} {GLYPH_BY_NAME['scope-open']} "
         f"0: \"zero\" 1: \"one\" _: \"many\" {GLYPH_BY_NAME['scope-close']}")
    a = (f"mch {x} {{ 0: \"zero\" 1: \"one\" _: \"many\" }}")
    p = (f"x = {x}\nprint({{0:'zero',1:'one'}}.get(x,'many'))")
    return g, a, p


def _tpl_alloc_free(v: int) -> tuple[str, str, str]:
    n = 1024 * (v + 1)
    g = (f"{GLYPH_BY_NAME['let']} p ({GLYPH_BY_NAME['alloc']} {n})\n"
         f"{GLYPH_BY_NAME['fence']} SEQ\n"
         f"{GLYPH_BY_NAME['free']} p")
    a = (f"let p (alc {n})\nfnc SEQ\nfre p")
    p = (f"import ctypes; buf = (ctypes.c_uint8 * {n})()")
    return g, a, p


def _tpl_perfctr_cpuid(v: int) -> tuple[str, str, str]:
    g = (f"{GLYPH_BY_NAME['let']} feat ({GLYPH_BY_NAME['cpu-feature']} 1)\n"
         f"{GLYPH_BY_NAME['let']} ctr ({GLYPH_BY_NAME['perfctr-rd']} {v})\n"
         f"{GLYPH_BY_NAME['write']} 1 ctr 8")
    a = (f"let feat (cpf 1)\nlet ctr (prf {v})\nwr 1 ctr 8")
    p = (f"import time; ctr = time.perf_counter_ns(); print(ctr)")
    return g, a, p


TEMPLATES: list[tuple[str, Any]] = [
    ("hello-world",                _tpl_hello_world),
    ("fizzbuzz",                   _tpl_fizzbuzz),
    ("fibonacci",                  _tpl_fibonacci),
    ("factorial",                  _tpl_factorial),
    ("list-map",                   _tpl_list_map),
    ("list-filter",                _tpl_list_filter),
    ("list-reduce",                _tpl_list_reduce),
    ("hashmap-iter",               _tpl_hashmap_iter),
    ("file-read",                  _tpl_file_read),
    ("file-write",                 _tpl_file_write),
    ("syscall-write",              _tpl_syscall_write),
    ("channel-send-recv",          _tpl_channel_send_recv),
    ("mutex",                      _tpl_mutex),
    ("atomic-cas",                 _tpl_atomic_cas),
    ("gpu-matmul-stub",            _tpl_gpu_matmul_stub),
    ("simulation-snapshot-step",   _tpl_simulation_snapshot_step),
    ("loop-break-continue",        _tpl_loop_break_continue),
    ("match-pattern",              _tpl_match_pattern),
    ("alloc-free",                 _tpl_alloc_free),
    ("perfctr-cpuid",              _tpl_perfctr_cpuid),
]


# ---------------------------------------------------------------------------
# Validation (Phase 1.5 fallback: regex check until parser ships)
# ---------------------------------------------------------------------------

# Tokenize ASCII source against the whole-token rule from GLYPH-SYNTAX.md
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_!]*|\+|\-|\*|/|%|&&|\|\||!")


def _has_at_least_one_glyph_or_ascii(src: str) -> bool:
    # Fast path: any glyph codepoint?
    for ch in src:
        if ch in ALL_GLYPH_CHARS:
            return True
    # Whole-token ASCII fallback check
    for tok in _TOKEN_RE.findall(src):
        if tok in ALL_ASCII_TOKENS:
            return True
    return False


def _validate_program(prog: dict) -> tuple[bool, str]:
    for required in ("filename", "glyph_src", "ascii_src"):
        if required not in prog:
            return False, f"missing field: {required}"
    if not isinstance(prog["filename"], str) or not prog["filename"]:
        return False, "filename must be non-empty string"
    if not _has_at_least_one_glyph_or_ascii(prog["glyph_src"]) and \
       not _has_at_least_one_glyph_or_ascii(prog["ascii_src"]):
        return False, "no recognized glyph or ASCII fallback in either source"
    return True, "ok"


# ---------------------------------------------------------------------------
# gen subcommand
# ---------------------------------------------------------------------------

def _make_program(template_idx: int, variant: int, kind: str) -> dict:
    name, fn = TEMPLATES[template_idx % len(TEMPLATES)]
    glyph_src, ascii_src, python_ref = fn(variant)
    if kind == "ascii":
        chosen = ascii_src
    elif kind == "glyph":
        chosen = glyph_src
    elif kind == "mixed":
        # Mixed = deterministic alternation across BOTH template index and variant
        # so a single batch sweep (variant=1, idx=0..N) still produces a mix.
        chosen = glyph_src if ((template_idx + variant) % 2 == 0) else ascii_src
    else:
        chosen = glyph_src
    filename = f"{name}-v{variant:03d}.shp"
    return {
        "filename": filename,
        "template": name,
        "variant": variant,
        "kind": kind,
        "glyph_src": glyph_src,
        "ascii_src": ascii_src,
        "python_ref": python_ref,
        "chosen_src": chosen,
        "bytes_glyph": len(glyph_src.encode("utf-8")),
        "bytes_ascii": len(ascii_src.encode("utf-8")),
        "bytes_python": len(python_ref.encode("utf-8")),
    }


def _gen_programs(count: int, kind: str) -> list[dict]:
    progs: list[dict] = []
    for i in range(count):
        t_idx = i % len(TEMPLATES)
        variant = (i // len(TEMPLATES)) + 1
        progs.append(_make_program(t_idx, variant, kind))
    return progs


def cmd_gen(args: argparse.Namespace) -> int:
    if args.kind not in ("ascii", "glyph", "mixed"):
        print(json.dumps({"status": "fail", "error": f"bad --kind: {args.kind}"}, indent=2))
        return 2

    progs = _gen_programs(int(args.count), args.kind)

    run_id = args.run_id or f"gen-{_utc_now()}"
    out_dir = _corpus_dir() / run_id

    result = {
        "subcommand": "gen",
        "dry_run": bool(args.dry_run),
        "kind": args.kind,
        "count_requested": int(args.count),
        "count_generated": len(progs),
        "run_id": run_id,
        "out_dir": str(out_dir),
        "templates_used": sorted({p["template"] for p in progs}),
        "total_bytes_glyph": sum(p["bytes_glyph"] for p in progs),
        "total_bytes_ascii": sum(p["bytes_ascii"] for p in progs),
        "total_bytes_python": sum(p["bytes_python"] for p in progs),
        "samples": progs[:2],  # echo first two for inspection
    }

    if args.dry_run:
        result["status"] = "dry-run"
        result["files_written"] = 0
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Real write
    out_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for p in progs:
        fp = out_dir / p["filename"]
        # If duplicate filename in same run (shouldn't happen but be safe), suffix
        if fp.exists():
            fp = out_dir / f"{p['filename'].replace('.shp', '')}-{uuid.uuid4().hex[:6]}.shp"
        fp.write_text(p["chosen_src"], encoding="utf-8")
        written += 1
    result["status"] = "ok"
    result["files_written"] = written
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# fanout subcommand
# ---------------------------------------------------------------------------

def cmd_fanout(args: argparse.Namespace) -> int:
    count = int(args.count)
    workers = max(1, int(args.workers))
    per_worker = max(1, count // workers)
    run_id = args.run_id or f"fanout-{_utc_now()}"

    slices = []
    issued = 0
    for i in range(workers):
        # Last worker absorbs any remainder
        n_this = per_worker if i < workers - 1 else (count - issued)
        if n_this <= 0:
            break
        sid = f"slice-{i:02d}"
        result_path = _swarm_results_dir() / f"hgly-seed-{run_id}" / f"{sid}.json"
        prompt = (
            "You are a Sinister Hieroglyphics corpus seed agent. "
            f"Emit {n_this} short .shp programs covering the 20 canonical "
            f"templates (hello-world, fizzbuzz, fibonacci, factorial, list-map, "
            f"list-filter, list-reduce, hashmap-iter, file-read, file-write, "
            f"syscall-write, channel-send-recv, mutex, atomic-cas, "
            f"gpu-matmul-stub, simulation-snapshot-step, loop-break-continue, "
            f"match-pattern, alloc-free, perfctr-cpuid). For each program "
            f"include {{filename, glyph_src, ascii_src, python_ref, "
            f"bytes_glyph, bytes_ascii, bytes_python}}. Write a JSON object "
            f"{{programs: [...]}} to {result_path} then exit. "
            f"See projects/sinister-hieroglyphics/docs/GLYPH-SYNTAX.md."
        )
        slices.append({
            "id": sid,
            "prompt": prompt,
            "owned_paths": [str(result_path)],
            "lane": "sinister-hieroglyphics",
            "programs_requested": n_this,
        })
        issued += n_this

    result = {
        "subcommand": "fanout",
        "dry_run": bool(args.dry_run),
        "count_requested": count,
        "workers": workers,
        "per_worker": per_worker,
        "run_id": run_id,
        "slices": slices,
        "swarm_results_dir": str(_swarm_results_dir() / f"hgly-seed-{run_id}"),
    }

    if args.dry_run:
        result["status"] = "dry-run (no swarm spawn)"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    # Real fan-out via sinister_swarm.fanout
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).parent))
        import sinister_swarm  # type: ignore
    except Exception as exc:
        result["status"] = "import-failed"
        result["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 3

    swarm_results = sinister_swarm.fanout(
        slug_prefix=f"hgly-seed-{run_id}",
        slices=slices,
        timeout_s=int(args.timeout_s),
        dry_run=False,
    )
    result["status"] = "dispatched"
    result["swarm_results"] = swarm_results
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# ingest subcommand
# ---------------------------------------------------------------------------

def _find_swarm_run_dir(run_id: Optional[str]) -> Optional[pathlib.Path]:
    root = _swarm_results_dir()
    if not root.exists():
        return None
    if run_id:
        # Try both naming conventions
        for prefix in (f"hgly-seed-{run_id}", run_id):
            cand = root / prefix
            if cand.exists():
                return cand
        return None
    # No id specified: pick most-recent hgly-seed-* directory
    candidates = sorted(
        [d for d in root.iterdir() if d.is_dir() and d.name.startswith("hgly-seed-")],
        key=lambda d: d.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


def cmd_ingest(args: argparse.Namespace) -> int:
    run_dir = _find_swarm_run_dir(args.run_id)
    result: dict[str, Any] = {
        "subcommand": "ingest",
        "dry_run": bool(args.dry_run),
        "run_id_requested": args.run_id,
        "swarm_run_dir": str(run_dir) if run_dir else None,
    }
    if run_dir is None or not run_dir.exists():
        result["status"] = "no-swarm-results"
        result["files_ingested"] = 0
        result["files_rejected"] = 0
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    derived_run_id = run_dir.name.replace("hgly-seed-", "", 1)
    out_dir = _corpus_dir() / derived_run_id

    ingested: list[str] = []
    rejected: list[dict] = []
    slices_seen = 0

    for slice_file in sorted(run_dir.glob("slice-*.json")):
        slices_seen += 1
        try:
            payload = json.loads(slice_file.read_text(encoding="utf-8"))
        except Exception as exc:
            rejected.append({"slice": slice_file.name, "reason": f"bad json: {exc}"})
            continue
        progs = payload.get("programs", [])
        if not isinstance(progs, list):
            rejected.append({"slice": slice_file.name, "reason": "programs not a list"})
            continue
        for prog in progs:
            ok, reason = _validate_program(prog)
            if not ok:
                rejected.append({"slice": slice_file.name, "filename": prog.get("filename"), "reason": reason})
                continue
            if args.dry_run:
                ingested.append(prog["filename"])
                continue
            out_dir.mkdir(parents=True, exist_ok=True)
            fp = out_dir / prog["filename"]
            if fp.exists():
                fp = out_dir / f"{prog['filename'].replace('.shp','')}-{uuid.uuid4().hex[:6]}.shp"
            # Prefer glyph_src; ASCII fallback if missing
            src = prog.get("glyph_src") or prog.get("ascii_src") or ""
            fp.write_text(src, encoding="utf-8")
            ingested.append(fp.name)

    result["status"] = "ok"
    result["slices_seen"] = slices_seen
    result["files_ingested"] = len(ingested)
    result["files_rejected"] = len(rejected)
    result["out_dir"] = str(out_dir) if not args.dry_run else None
    result["rejected_samples"] = rejected[:5]
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# stats subcommand
# ---------------------------------------------------------------------------

def _glyph_coverage(text: str, counts: dict[str, int]) -> None:
    # Count glyph occurrences
    for ch in text:
        if ch in ALL_GLYPH_CHARS:
            counts[ch] = counts.get(ch, 0) + 1
    # Count ASCII fallback tokens (whole tokens only)
    for tok in _TOKEN_RE.findall(text):
        if tok in ALL_ASCII_TOKENS:
            counts[tok] = counts.get(tok, 0) + 1


def cmd_stats(args: argparse.Namespace) -> int:
    cdir = _corpus_dir()
    files: list[pathlib.Path] = []
    if cdir.exists():
        files = sorted(cdir.glob("**/*.shp"))

    total_bytes = 0
    counts: dict[str, int] = {}
    per_file: list[dict] = []
    for fp in files:
        try:
            data = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        b = len(data.encode("utf-8"))
        total_bytes += b
        _glyph_coverage(data, counts)
        per_file.append({"path": str(fp.relative_to(cdir)), "bytes": b})

    file_count = len(files)
    mean_bytes = (total_bytes / file_count) if file_count else 0.0

    # Build histogram in canonical glyph order
    histogram: list[dict] = []
    for (idx, glyph, ascii_fb, name, category) in GLYPHS:
        n_glyph = counts.get(glyph, 0)
        n_ascii = counts.get(ascii_fb, 0)
        if n_glyph + n_ascii == 0:
            continue
        histogram.append({
            "idx": idx,
            "name": name,
            "category": category,
            "glyph_count": n_glyph,
            "ascii_count": n_ascii,
            "total": n_glyph + n_ascii,
        })

    glyphs_covered = len(histogram)
    coverage_pct = round(100.0 * glyphs_covered / 64.0, 2)

    result = {
        "subcommand": "stats",
        "dry_run": bool(args.dry_run),
        "corpus_dir": str(cdir),
        "corpus_exists": cdir.exists(),
        "file_count": file_count,
        "total_bytes": total_bytes,
        "mean_bytes_per_program": round(mean_bytes, 2),
        "glyph_vocabulary_size": 64,
        "glyphs_covered": glyphs_covered,
        "coverage_pct": coverage_pct,
        "histogram_top20": sorted(histogram, key=lambda r: -r["total"])[:20],
        "files_top20_by_size": sorted(per_file, key=lambda r: -r["bytes"])[:20],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _add_dry(p: argparse.ArgumentParser) -> None:
    p.add_argument("--dry-run", action="store_true")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hgly_corpus_seed",
        description="Bootstrap + grow the Sinister Hieroglyphics training corpus.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("gen", help="local deterministic generation (no swarm)")
    _add_dry(p_gen)
    p_gen.add_argument("--count", type=int, required=True)
    p_gen.add_argument("--kind", choices=["ascii", "glyph", "mixed"], default="mixed")
    p_gen.add_argument("--run-id", default=None)

    p_fan = sub.add_parser("fanout", help="multi-agent parallel generation via sinister_swarm")
    _add_dry(p_fan)
    p_fan.add_argument("--count", type=int, required=True)
    p_fan.add_argument("--workers", type=int, default=4)
    p_fan.add_argument("--timeout-s", type=int, default=600)
    p_fan.add_argument("--run-id", default=None)

    p_ing = sub.add_parser("ingest", help="read swarm-results, validate, write to corpus")
    _add_dry(p_ing)
    p_ing.add_argument("--run-id", default=None)

    p_stat = sub.add_parser("stats", help="corpus file count + bytes + glyph histogram")
    _add_dry(p_stat)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dispatch = {
        "gen": cmd_gen,
        "fanout": cmd_fanout,
        "ingest": cmd_ingest,
        "stats": cmd_stats,
    }
    fn = dispatch[args.cmd]
    return fn(args)


if __name__ == "__main__":
    sys.exit(main())
