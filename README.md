# Civic Preflight — offline Spanish form checker

A local, read-only CLI written in the **Salam Programming Language**. Designed to detect likely typos in common Spanish administrative-form fields before a human reviews and submits a form.

**Privacy:** no network use, no identity verification, no storage of inspected records, no printing DNI/NIE/email values. The original file is never modified. Use only for your own data or data you are authorized to process.

Checks planned:
- DNI and NIE syntax and check letter
- Five-digit Spanish postcode and province prefix
- Gregorian appointment dates including leap years
- Basic email typography (not deliverability)
- Duplicate record references, TSV structure and empty required fields

This program cannot confirm legal identity, document validity/expiry, appointment availability, entitlement, or actual postal delivery.

Build and test information is added in incremental development commits.

Upstream language: [SalamLang/Salam](https://github.com/SalamLang/Salam).

AI assistance: source implementation and tests are AI-assisted, with executable verification recorded rather than claiming unaudited human review.
