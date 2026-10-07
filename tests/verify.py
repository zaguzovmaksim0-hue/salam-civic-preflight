#!/usr/bin/env python3
"""Black-box tests against the native Salam executable; synthetic data only."""
from __future__ import annotations

import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BIN = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / ".cache" / "civic-preflight"
HEADER = "reference\tdocument_id\tpostal_code\tappointment_date\temail\n"
GOOD = ("ref-A", "12345678Z", "11001", "2026-11-05", "a@example.org")
passed = 0
failed = 0


def invoke(content: bytes) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="civic-test-") as directory:
        path = Path(directory) / "input.tsv"
        path.write_bytes(content)
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        run = subprocess.run([str(BIN), str(path)], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", errors="replace", timeout=8)
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        if before != after:
            raise AssertionError("source file was modified")
        return run


def check(label: str, content: bytes, expected: int,
          fragment: str | None = None) -> None:
    global passed, failed
    try:
        run = invoke(content)
        if run.returncode != expected:
            raise AssertionError(f"wanted exit {expected}, got {run.returncode}, stdout={run.stdout!r}, stderr={run.stderr!r}")
        if fragment and fragment not in run.stdout:
            raise AssertionError(f"missing {fragment!r} in {run.stdout!r}")
        if any(secret in run.stdout + run.stderr for secret in
               ["12345678Z", "12345678A", "SENSITIVE@example.org"]):
            raise AssertionError("input identity/email leaked into program output")
        passed += 1
        print(f"PASS {label}")
    except Exception as exc:
        failed += 1
        print(f"FAIL {label}: {exc}")


def line(*fields: str) -> bytes:
    return (HEADER + "\t".join(fields) + "\n").encode("utf-8")


def vary(index: int, value: str) -> bytes:
    fields = list(GOOD)
    fields[index] = value
    return line(*fields)


def direct(label: str, args: list[str], code: int, fragment: str) -> None:
    global passed, failed
    try:
        p = subprocess.run([str(BIN), *args], cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=8)
        assert p.returncode == code and fragment in p.stdout, (p.returncode, p.stdout, p.stderr)
        passed += 1
        print(f"PASS {label}")
    except Exception as exc:
        failed += 1
        print(f"FAIL {label}: {exc}")


if not BIN.exists():
    print("ERROR: build first:", BIN, file=sys.stderr)
    sys.exit(2)
check("valid DNI sample", line(*GOOD), 0, "Result: PASS")
check("valid NIE X", vary(1, "X1234567L"), 0)
check("valid NIE Y", vary(1, "Y1234567X"), 0)
check("valid NIE Z", vary(1, "Z1234567R"), 0)
check("DNI lower-case check letter", vary(1, "12345678z"), 0)
check("NIE lower-case prefix", vary(1, "x1234567l"), 0)
check("DNI zero prefix", vary(1, "00000000T"), 0)
check("NIE X zero prefix", vary(1, "X0000000T"), 0)
check("DNI invalid letter", vary(1, "12345678A"), 1, "DNI/NIE checks:  1")
check("DNI missing letter", vary(1, "12345678"), 1)
check("DNI non-numeric", vary(1, "123A5678Z"), 1)
check("NIE bad prefix", vary(1, "Q1234567L"), 1)
check("NIE bad check letter", vary(1, "X1234567A"), 1)
check("NIE bad numeric field", vary(1, "X1234A67L"), 1)
check("empty identity", vary(1, ""), 1)
check("post zero-prefixed province", vary(2, "01001"), 0)
check("post upper province", vary(2, "52001"), 0)
check("post province 00", vary(2, "00001"), 1, "Postcode checks:  1")
check("post province 53", vary(2, "53001"), 1)
check("post missing digit", vary(2, "1100"), 1)
check("post invalid letter", vary(2, "11a01"), 1)
check("post extra digit", vary(2, "110010"), 1)
check("date leap 2000", vary(3, "2000-02-29"), 0)
check("date leap 2024", vary(3, "2024-02-29"), 0)
check("date non-leap 1900", vary(3, "1900-02-29"), 1, "Date checks:  1")
check("date non-leap 2100", vary(3, "2100-02-29"), 1)
check("date November day 31", vary(3, "2026-11-31"), 1)
check("date invalid month 13", vary(3, "2026-13-01"), 1)
check("date invalid month zero", vary(3, "2026-00-01"), 1)
check("date invalid year zero", vary(3, "0000-01-01"), 1)
check("date invalid day zero", vary(3, "2026-01-00"), 1)
check("date invalid text", vary(3, "2026/11/05"), 1)
check("date invalid digit", vary(3, "2026-1a-05"), 1)
check("date year 9999", vary(3, "9999-12-31"), 0)
check("email optional", vary(4, ""), 0)
check("email plus tag", vary(4, "first+tag@example.co.uk"), 0)
check("email missing @", vary(4, "first.example.com"), 1)
check("email missing domain dot", vary(4, "a@example"), 1)
check("email multiple @", vary(4, "a@b@example.com"), 1)
check("email consecutive dots user", vary(4, "a..b@example.org"), 1)
check("email consecutive dots domain", vary(4, "a@example..org"), 1)
check("email whitespace", vary(4, "SENSITIVE@example.org  bad"), 1)
check("email at missing user", vary(4, "@example.org"), 1)
check("email domain dot first", vary(4, "a@.example.org"), 1)
check("email dot last", vary(4, "a@example.org."), 1)
check("empty reference", vary(0, ""), 1, "Empty references:  1")
check("duplicate ref case-insensitive", line(*GOOD) + b"ref-a\t12345678Z\t11001\t2026-11-06\tother@example.org\n",
      1, "Duplicate references:  1")
check("malformed too few columns", HEADER.encode() + b"ref-A\t12345678Z\n", 1, "Malformed rows:  1")
check("malformed extra columns", HEADER.encode() + b"\t".join([b"x"] * 6) + b"\n", 1)
check("blank line only", HEADER.encode(), 1, "no records")
check("UTF-8 BOM", b"\xef\xbb\xbf" + line(*GOOD), 0)
check("CRLF", line(*GOOD).replace(b"\n", b"\r\n"), 0)
check("comment after header", HEADER.encode() + b"# local comment\n" + b"\t".join(s.encode() for s in GOOD) + b"\n", 0)
check("hash-leading valid reference is data", line("#reference", "12345678Z", "11001", "2026-11-05", "a@example.org"), 0)
check("hash-leading malformed row not suppressed", HEADER.encode() + b"#ref\tbad\n", 1, "Malformed rows:  1")
check("blank rows between records", HEADER.encode() + b"\n" + b"\t".join(s.encode() for s in GOOD) + b"\n", 0)
check("header wrong order", HEADER.replace("postal_code", "postcode").encode(), 2, "expected TSV header")
check("header absent", b"no header\n", 2)
check("header empty", b"", 2)
check("binary NUL truncation", line(*GOOD) + b"\x00", 2, "cannot read source")
check("oversize input", HEADER.encode() + b"x" * 2097152, 2, "cannot read source")
check("multiple issues one record",
      line("","12345678A","53000","1900-02-29","SENSITIVE@example.org  bad"),
      1, "Total issue occurrences:  5")
direct("help", ["--help"], 0, "Usage:")
direct("version", ["--version"], 0, "0.1.0")
direct("usage missing arg", [], 2, "Usage:")
direct("missing input file", ["__nonexistent_civic_input_1628__.tsv"], 2, "cannot read source")
direct("too many args", ["a.tsv", "b.tsv"], 2, "Usage:")

print(f"\nSummary: {passed} PASS, {failed} FAIL")
sys.exit(0 if failed == 0 else 1)
