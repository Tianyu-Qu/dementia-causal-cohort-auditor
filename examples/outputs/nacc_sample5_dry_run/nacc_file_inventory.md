# NACC File Inventory

This inventory summarizes file structure and small-sample distributions only. It does not print participant-level rows.

| File | Rows | Columns | Inferred grain | Key sample summaries |
| --- | ---: | ---: | --- | --- |
| followup_status.csv | 5 | 4 | participant_or_module | NACCID: {'unique_in_sample': 5, 'missing_in_sample': 0} |
| medications.csv | 5 | 7 | visit_or_longitudinal | NACCID: {'unique_in_sample': 5, 'missing_in_sample': 0}; NACCVNUM: {'1': 5}; UDSVER: {'3': 5}; CURRENT_USE: {'1': 5} |
| participants.csv | 5 | 5 | participant_or_module | NACCID: {'unique_in_sample': 5, 'missing_in_sample': 0}; SEX: {'2': 3, '1': 2}; NACCNE4S: {'1': 2, '0': 1, '9': 1, '2': 1} |
| uds_visits.csv | 5 | 11 | visit_or_longitudinal | NACCID: {'unique_in_sample': 3, 'missing_in_sample': 0}; NACCVNUM: {'1': 3, '2': 2}; VISITYR: {'2020': 3, '2021': 2}; NACCAGE: {'70': 1, '71': 1, '68': 1, '69': 1, '72': 1}; UDSVER: {'3': 5}; NACCUDSD: {'1': 3, '2': 2}; CDRGLOB: {'0': 3, '0.5': 2}; CDRSUM: {'0': 2, '0.5': 1, '1.5': 1, '2': 1}; NACCMMSE: {'29': 1, '28': 1, '27': 1, '26': 1, '30': 1} |
