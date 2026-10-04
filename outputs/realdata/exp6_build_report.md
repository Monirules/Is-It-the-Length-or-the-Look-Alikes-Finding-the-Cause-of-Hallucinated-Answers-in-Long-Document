# Exp 6 data, part 2: documents with look-alike or random Wikipedia passages

300 questions x 5 settings = **1500 documents**, in `/home/monirul/nullscale_work/data/nq/exp6`.

Every no-gold document was checked: no answer string, no passage of the gold article. Every control document contains its answer. Every length is within 1% of its target.

| setting | documents | tokens (mean) | passages (mean) | similarity to the question (mean BM25) | gold position (mean) |
|---|---|---|---|---|---|
| gold_present_8k | 300 | 7,974 | 57 | 19.48 | 0.50 |
| no_gold_lookalike_8k | 300 | 7,976 | 57 | 19.44 | - |
| no_gold_random_8k | 300 | 7,977 | 56 | 0.35 | - |
| no_gold_lookalike_32k | 300 | 31,896 | 226 | 15.68 | - |
| no_gold_random_32k | 300 | 31,898 | 225 | 0.34 | - |

Look-alike documents should score clearly higher on similarity than random ones; that is the manipulation Exp 6 tests.

## Examples

- **Southern soul was considered the sound of what independent record label?** (answer: Motown; gold article removed: Motown; Soul music)
  - top look-alike articles: Wackies; Capricorn Records; Record Kicks; Record Kicks; New York soul
  - random articles: Rollie Williams; Royal Princess (2012); Hello (Kelly Clarkson song); 2019 FIBA Basketball World Cup qualification (Americas); Connie Mitchell
- **Who won i want to work for diddy?** (answer: Suzanne Siegel; gold article removed: I Want to Work for Diddy (season 1))
  - top look-alike articles: I Want to Work for Diddy 2; I Want to Work for Diddy 2; Laverne Cox; Transamerican Love Story; Transamerican Love Story
  - random articles: SI derived unit; Flubber (film); Jon Snow (character); British Isles; Michael Langhi
- **Who was the first woman appointed to the supreme court?** (answer: Sandra Day O'Connor; gold article removed: Burger Court; Demographics of the Supreme Court of the United States)
  - top look-alike articles: Kaïta Kayentao Diallo; Mary Yu; All-Woman Supreme Court; Mata Tuatagaloa; Mata Tuatagaloa
  - random articles: Butte La Rose, Louisiana; Himno Nacional Mexicano; Devotion + Doubt; Gregory Snegoff; Anal gland
