# Look-alike records in RIKER2's trap questions

Made by riker/find_lookalikes.py. A look-alike record matches the asked record's key (names, date) in every part but one; for L12 it must also have the asked field. See the script's docstring for the rules.

539 trap questions; 0 could not be read (unparsed).

## Look alike present, by length and level

| length | level | questions | look alike present | no look alike | of which weak (one part of the key matches) | mean look-alike records per question |
|---|---|---|---|---|---|---|
| 32K | L11 | 63 | 63 (100%) | 0 | 0 | 1.24 |
| 32K | L12 | 63 | 17 (27%) | 46 | 12 | 0.35 |
| 32K | all | 126 | 80 (63%) | 46 | 12 | 0.79 |
| 128K | L11 | 90 | 90 (100%) | 0 | 0 | 1.22 |
| 128K | L12 | 90 | 22 (24%) | 68 | 48 | 0.34 |
| 128K | all | 180 | 112 (62%) | 68 | 48 | 0.78 |
| 200K | L11 | 116 | 116 (100%) | 0 | 0 | 1.22 |
| 200K | L12 | 117 | 26 (22%) | 91 | 57 | 0.31 |
| 200K | all | 233 | 142 (61%) | 91 | 57 | 0.76 |

## By document type (all lengths)

| document type | level | questions | present | kinds of the closest look-alike |
|---|---|---|---|---|
| field_report | L11 | 60 | 60 | other_party 60 |
| field_report | L12 | 60 | 15 | none 45, other_date 12, other_party 3 |
| hr | L11 | 60 | 60 | shared_name 60 |
| hr | L12 | 60 | 50 | other_date 50, none 10 |
| lease_document | L11 | 149 | 149 | other_party 149 |
| lease_document | L12 | 150 | 0 | none 150 |

Look-alike records found in the document text: 334 of 334 questions with a look-alike.
Position of the closest look-alike in the document (0 = start, 1 = end): median 0.43, range 0.00-1.00
L11 questions where every asked name is in the text (no made-up name found): 19

## Examples

- 32K `field_report_L12_T15_0013` (other_date): What is the follow-up reason in Nikhaule Hesla's field report about Tyzjuan Usilton on 2024-02-29?  -> look-alike FR_00025, value `discuss lease terms in more detail`
- 32K `hr_L12_T03_0001` (other_date): What is written under "Manager Comments:" in Chela Woerth's evaluation for December 2024?  -> look-alike HR_00011, value `Goes above and beyond consistently. Valuable asset to the organization.`
- 32K `hr_L11_T01_0001` (shared_name): When was Kylor Hesla's evaluation for June 2025 conducted?  -> look-alike HR_00029, value `2025-07-08`
- 32K `hr_L11_T01_0002` (shared_name): What is the performance rating in Maecy Hugeback's evaluation for June 2024?  -> look-alike HR_00004, value `Exceeds Expectations`
- 32K `field_report_L11_T15_0001` (other_party): Does Adelore Wurgler's field report about Diani Kosofsky on 2024-08-28 include property condition notes?  -> look-alike FR_00037, value `No`
- 32K `field_report_L11_T15_0002` (other_party): Does Brianamarie Colagrossi's field report about Drilon Friermood on 2024-09-21 mention a competitor property?  -> look-alike FR_00043, value `No`
- 32K `field_report_L12_T15_0001` (no look-alike): Who is the manager that commented on Kylor Rauseo's field report about Tessalee Kilcoin on 2025-04-08?  -> look-alike -, value `None`
- 32K `field_report_L12_T15_0002` (no look-alike): What are the manager's comments in Nikhaule Hesla's field report about Tyzjuan Usilton on 2024-02-29?  -> look-alike -, value `None`
