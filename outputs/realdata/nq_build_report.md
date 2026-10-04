# Exp 6 data, part 1: Natural Questions with the answer removed

Source: `Tevatron/wikipedia-nq` / `nq-dev.jsonl.gz` (DPR's open-domain Natural Questions, dev split). Seed 20267012.

- questions read: 6,489; qualifying: 6,180; **chosen: 300**
- Wikipedia pool for retrieve.py: 533,872 distinct 100-word passages
- passages removed from the chosen questions' similar lists: 2,239 positive (gold), 173 holding an answer string, 2,434 from the gold article
- similar passages left per question: min 40, median 89, max 100

## Ten examples

| # | question | answers | gold article | similar passages left |
|---|---|---|---|---|
| 0 | Southern soul was considered the sound of what independent record label? | Motown | Motown; Soul music | 95 |
| 1 | Who won i want to work for diddy? | Suzanne Siegel | I Want to Work for Diddy (season 1) | 98 |
| 2 | Who was the first woman appointed to the supreme court? | Sandra Day O'Connor | Burger Court; Demographics of the Supreme Court of the United States | 95 |
| 3 | Who sings i 'm back in the saddle again? | Gene Autry | Back in the Saddle (film); Back in the Saddle Again | 89 |
| 4 | When was the last time university of michigan won the ncaa men 's basketball tournament? | 1989 | 1988–89 Michigan Wolverines men's basketball team; 1989 NCAA Division I Men's Basketball Championship Game | 88 |
| 5 | Who sings i want to rock with you? | Michael Jackson | Boyfriend (Justin Bieber song); Rock with You | 99 |
| 6 | When was the last time the seattle seahawks went to the superbowl? | 2014 | 1996 NBA Finals; 2014 Seattle Seahawks season | 87 |
| 7 | When did jackie robinson retire from the brooklyn dodgers? | 1956 | Don Hoak; Droyer's Point | 88 |
| 8 | Who ensures that the states abide by constitutional and federal law? | Supreme Court | Adamson Act; Apodaca v. Oregon | 67 |
| 9 | Who played spock 's dad on star trek? | Mark Lenard | Here Come the Brides; Sarek | 99 |
