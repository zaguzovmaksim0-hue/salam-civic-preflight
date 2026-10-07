# Civic Preflight

**Private, offline preflight checks for Spanish administrative-form data.** Built with the [Salam Programming Language](https://github.com/SalamLang/Salam).

Civic Preflight reads a TSV file and reports possible field-entry mistakes with physical line numbers. It checks **DNI/NIE control letters**, Spanish postcode structure, real Gregorian dates, basic email typography, duplicated record references and malformed rows. It never edits the input file, transmits data or echoes document numbers and email addresses in its diagnostics.

This is a local quality-control tool — **not an official government validator**. A correct DNI/NIE check letter does **not** prove that the document exists, is genuine, belongs to someone, or remains valid. A plausible five-digit postcode does **not** prove an address exists. The tool does not check actual appointments, legal eligibility or email deliverability.

## Quick start

Install [Salam v0.5.0](https://github.com/SalamLang/Salam/releases/tag/v0.5.0), a C compiler such as GCC, and Python 3 for the test suite:

```sh
mkdir -p .cache
salam build src/main.salam --backend=c --cc=gcc --output=.cache/civic-preflight
.cache/civic-preflight examples/sample.tsv
python3 tests/verify.py .cache/civic-preflight
```

On Windows, change the output to a native `.exe` and run using Windows path conventions. The verified build environment is Linux ARM64 (Debian userspace on Android Termux), Salam 0.5.0, GCC and Python 3. The GitHub Actions Linux x64 job runs the same source-level tests.

## File format

**UTF-8 tab-separated values** with this *exact* first-line header:

```tsv
reference	document_id	postal_code	appointment_date	email
case-001	12345678Z	11001	2026-11-05	example@example.org
case-002	X1234567L	28001	2024-02-29	
```

These are synthetic identifiers for testing, not records of actual people. A valid row has five fields, including a possibly blank email. The reference, DNI/NIE, postcode and appointment date are required.

- `reference`: any nonblank local record key; case-insensitive duplicates are flagged, and only line numbers are reported.
- `document_id`: DNI = eight digits and a control letter; NIE = X/Y/Z, seven digits and a control letter. ASCII letter case is normalized for comparison. No internal hyphens/spaces.
- `postal_code`: five ASCII digits, with province/city prefix 01–52; existence of an actual delivery route is **not** verified.
- `appointment_date`: strictly ISO `YYYY-MM-DD` and a valid Gregorian calendar day; dates need not be in the future.
- `email`: optional, minimal typo checks, **not** full RFC validation or a mailbox reachability test.

UTF-8 BOM and CRLF line endings are supported. Blank lines and comment lines beginning with `#` **without tabs** are ignored; five-field rows beginning with `#` are still inspected. Files larger than 2 MiB, truncated/binary reads, invalid header order and unreadable paths are rejected.

## Output, privacy and exit codes

A sample diagnostic might be:

```text
ERROR line 3: invalid DNI/NIE shape or control letter
ERROR line 4: repeated reference; first seen at line 2
...
Result: REVIEW
Note: check digits and formats never prove identity, address or booking.
```

Output contains physical **line numbers and rule names**, not the original record values. The tool keeps duplicate-reference keys only in memory for the duration of the run and creates no output file. It makes no network requests. You remain responsible for securely storing or deleting the source TSV.

| Exit | Meaning |
| ---: | --- |
| `0` | All inspected records passed the limited checks; or help/version shown |
| `1` | At least one record needs review (including no records) |
| `2` | CLI usage, file read, size, or header problem |

## Code organization

`src/` includes separate, purposeful modules: CLI, data model, normalization, bounded file reader, TSV parser, DNI checksum, NIE checksum, document dispatch, postal prefix check, Gregorian calendar, email typography, reference deduplication, rules engine and privacy-preserving report. `tests/verify.py` runs deterministic native black-box cases with temporary synthetic TSV and checks that input hashes remain unchanged.

## Primary references and limitations

- [Ministerio del Interior — cálculo del dígito de control NIF/NIE](https://www.interior.gob.es/opencms/es/servicios-al-ciudadano/tramites-y-gestiones/dni/calculo-del-digito-de-control-del-nif-nie): modulo-23 mapping and NIE X/Y/Z substitution.
- [Agencia Tributaria — composición del DNI/NIE](https://sede.agenciatributaria.gob.es/Sede/ayuda/consultas-informaticas/firma-digital-sistema-clave-pin-tecnica/identificarte-mediante-numero-dni-nie-contraste.html): canonical document shape without spaces/hyphens.
- [BOE-A-1984-3487](https://www.boe.es/buscar/doc.php?id=BOE-A-1984-3487): postal codes contain five digits; the first two denote the province.
- [BOE-A-1995-21835](https://www.boe.es/buscar/doc.php?id=BOE-A-1995-21835): Ceuta and Melilla prefixes 51 and 52.

No exhaustive Correos postcode database is shipped or inferred. Email checks are heuristic. The user must independently verify any consequential administrative submission.

## Development and licensing

Copyright (c) 2026 Maksim Zaguzov. Licensed under [MIT](LICENSE). Contributions should include runnable tests and should not introduce telemetry, network transmission of record contents or output of raw identifiers.

**AI development disclosure:** implementation, documentation and tests were created with AI assistance on the GitHub account holder's behalf. No independent human technical review is claimed. Compilation and automated test outcomes are reported only where actually executed.
