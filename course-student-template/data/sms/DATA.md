# SMS package metadata

Source: UCI SMS Spam Collection, Almeida and Hidalgo (2011), DOI 10.24432/C5CC84.
Upstream catalog URL: https://archive.ics.uci.edu/dataset/228/sms+spam+collection
License record: CC BY 4.0 (UCI catalog), checked in the historical source record dated 2026-10-11.

## Files present in this student package

`train.csv`, `dev.csv`, `split_manifest.csv`, `provenance.json`, `DATA.md`.

|File|Rows|Groups|Columns|
|---|---:|---:|---|
|train.csv|3877|3501|id, label, text, text_sha256, group_id, split|
|dev.csv|807|711|id, label, text, text_sha256, group_id, split|
|split_manifest.csv|5574|4985|id, text_sha256, group_id, split|

Train label counts: ham 3365, spam 512. Dev label counts: ham 684, spam 123.
The split manifest contains ID, original text hash, group ID, and split metadata only; it contains neither text nor labels. It includes 890 historical finalholdout IDs.
Train and dev share no group IDs, record IDs, or original-text hashes.

## Current data SHA-256

- `train.csv`: `3d4c268e8bba99a5dd4bcd806b084d322ad0fb3f404db041109cc1f7d18b26fb`
- `dev.csv`: `21602715697e834fc1e69ea9eeb7ae2c280fb2a06833848f48940626e02ac5c6`
- `split_manifest.csv`: `686ee5e28cc33d749f25ca1d170e550b700f80629b2c262986751a0a11b9cd0d`

## Historical source records

Historical source commit: `912ade66c5449bfd740277bc761de7b9b54154fd`.
The nested `historical_source` object in `provenance.json` records original source totals, grouping, and hashes. Those records do not imply that referenced files are included here.
No upstream full corpus, source ZIP, finalholdout text or labels, encoder, or embedding cache is included in this student package.

The original English readme is retained byte-for-byte in the course repository teacher resource path `course-instructor/lessons/S08/resources/original-sms-readme.txt`, outside this student package. It contains labelled examples that match historical finalholdout texts. Its SHA-256 is `8753cd2d3cab68f80c8257851b8c2037778c267f55accb6fd1b5a2e32d36a84e`.

## Runtime metadata

The local lesson-10 baseline uses the fixed manual representation and NumPy. Its loader checks the current `file_sha256` keys for train/dev. It accepts only train and dev partitions.
Grouping recorded by the historical source: normalization and exact/near-duplicate grouping before group-level splitting, seed 20261011. No chronological order or sender identity is supplied.
