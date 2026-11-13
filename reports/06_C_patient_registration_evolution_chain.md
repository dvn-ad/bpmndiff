# Version chain

Registration of old patients → General new patient registration → Corporate new patient registration

## Consecutive steps

| Step | Transition | Verdict | Trace equiv. | Operations |
|---|---|---|---|---|
| 1 | Registration of old patients → General new patient registration | semantic_and_behavioral_change | no | {'DELETE': 2, 'INSERT': 2, 'RENAME': 2, 'DELETE_FLOW': 1, 'INSERT_FLOW': 4} |
| 2 | General new patient registration → Corporate new patient registration | semantic_and_behavioral_change | no | {'INSERT': 1, 'RENAME': 1, 'DELETE_FLOW': 1, 'INSERT_FLOW': 2} |

## Reverts (0)

_None detected._

## Transitivity oracle

- Consistent: **True**
- Discrepancies: 0