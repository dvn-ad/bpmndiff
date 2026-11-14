# Reference vs. many variants

Reference: **General new patient registration**

| Variant | Verdict | Trace equivalence | Operations |
|---|---|---|---|
| Corporate new patient registration | semantic_and_behavioral_change | no | {'INSERT': 1, 'RENAME': 1, 'DELETE_FLOW': 1, 'INSERT_FLOW': 2} |
| General inpatient registration | semantic_and_behavioral_change | no | {'DELETE': 1, 'INSERT': 13, 'RENAME': 6, 'CHANGE_SWIMLANE': 2, 'DELETE_FLOW': 7, 'INSERT_FLOW': 23} |
| Corporate inpatient registration | semantic_and_behavioral_change | no | {'DELETE': 1, 'INSERT': 13, 'RENAME': 6, 'CHANGE_SWIMLANE': 1, 'DELETE_FLOW': 2, 'INSERT_FLOW': 18} |

## Core elements (11)

- <start event>
- Wants to register a new general patient
- Displays a registration form
- <end event>
- Enters the patient's identity
- <exclusive gateway (XOR)>
- Saves the registration information
- <exclusive gateway (XOR)>
- Selects the register button
- Enter the patient's address
- displays the registration information to a table in the form

## Variant-specific elements (1)

- Queries District, Subdistric, Village, and Referral — present in Corporate new patient registration