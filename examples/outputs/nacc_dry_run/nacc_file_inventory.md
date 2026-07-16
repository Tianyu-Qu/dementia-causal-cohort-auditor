# NACC File Inventory

This inventory summarizes file structure and small-sample distributions only. It does not print participant-level rows.

| File | Rows | Columns | Inferred grain | Key sample summaries |
| --- | ---: | ---: | --- | --- |
| followup_status.csv | 9 | 4 | participant_or_module | NACCID: {'unique_in_sample': 9, 'missing_in_sample': 0} |
| medications.csv | 9 | 7 | visit_or_longitudinal | NACCID: {'unique_in_sample': 9, 'missing_in_sample': 0}; NACCVNUM: {'1': 9}; UDSVER: {'3': 7, '4': 2}; CURRENT_USE: {'1': 9} |
| participants.csv | 9 | 5 | participant_or_module | NACCID: {'unique_in_sample': 9, 'missing_in_sample': 0}; SEX: {'2': 5, '1': 4}; NACCNE4S: {'1': 4, '0': 3, '9': 1, '2': 1} |
| uds_visits.csv | 18 | 11 | visit_or_longitudinal | NACCID: {'unique_in_sample': 9, 'missing_in_sample': 0}; NACCVNUM: {'1': 10, '2': 8}; VISITYR: {'2020': 10, '2021': 8}; NACCAGE: {'70': 2, '69': 2, '75': 2, '74': 2, '71': 1, '68': 1, '72': 1, '73': 1, '80': 1, '81': 1}; UDSVER: {'3': 14, '4': 4}; NACCUDSD: {'1': 11, '2': 3, '4': 2, '-4': 2}; CDRGLOB: {'0': 11, '0.5': 3, '-4': 2, '1': 1, '2': 1}; CDRSUM: {'0': 9, '0.5': 2, '2': 2, '-4': 2, '1.5': 1, '5': 1, '8': 1}; NACCMMSE: {'29': 6, '28': 3, '-4': 3, '27': 1, '26': 1, '30': 1, '20': 1, '18': 1, '25': 1} |
