# bpmndiff demo report

Dataset: `/home/mendoan/Projects/bpmndiff/BPMN Diagrams Dataset of Functional Requirements/XPDL Dataset`

| Scenario | Mode | Verdict | Trace equivalent | Details |
|---|---|---|---|---|
| Taxonomy 1: Steps (Tasks and Events) | A | semantic_and_behavioral_change | no | 9 operations |
| Taxonomy 2: Actors (Lanes and Pools) | A | non_behavioral_swimlane_change | yes | 3 operations |
| Taxonomy 3: Sequence, Flow, and Branching | A | behavioral_change | no | 21 operations |
| Taxonomy 4: Sub-process Structure | A | semantic_and_behavioral_change | no | 11 operations |
| Taxonomy 5: Data and Cross-Pool Communication | A | unchanged | yes | 3 operations |
| Old vs. new patient registration | A | semantic_and_behavioral_change | no | 12 operations |
| General vs. corporate new patient registration | A | semantic_and_behavioral_change | no | 5 operations |
| General vs. corporate inpatient registration | A | semantic_change | yes | 3 operations |
| General patient cashier vs. down payment | A | semantic_and_behavioral_change | no | 45 operations |
| Patient registration family | B | semantic_and_behavioral_change, semantic_and_behavioral_change, semantic_and_behavioral_change | no | 11 core elements |
| Patient registration evolution chain | C | semantic_and_behavioral_change -> semantic_and_behavioral_change | no | 0 reverts, oracle consistent=True |

## Scenario details

### Taxonomy 1: Steps (Tasks and Events)

- Mode: A
- Models: Patient Registration (v1), Patient Registration (v2)
- Verdict: **semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 9 operations
- Report: [01_A_taxonomy_1__steps__tasks_and_events.md](01_A_taxonomy_1__steps__tasks_and_events.md)

### Taxonomy 2: Actors (Lanes and Pools)

- Mode: A
- Models: Payment Settlement (v1), Payment Settlement (v2)
- Verdict: **non_behavioral_swimlane_change**
- Trace equivalent: True
- Details: 3 operations
- Report: [02_A_taxonomy_2__actors__lanes_and_pools.md](02_A_taxonomy_2__actors__lanes_and_pools.md)

### Taxonomy 3: Sequence, Flow, and Branching

- Mode: A
- Models: Patient Discharge (v1), Patient Discharge (v2)
- Verdict: **behavioral_change**
- Trace equivalent: False
- Details: 21 operations
- Report: [03_A_taxonomy_3__sequence__flow__and_branching.md](03_A_taxonomy_3__sequence__flow__and_branching.md)

### Taxonomy 4: Sub-process Structure

- Mode: A
- Models: Clinical and Billing Check (v1), Clinical and Billing Check (v2)
- Verdict: **semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 11 operations
- Report: [04_A_taxonomy_4__sub_process_structure.md](04_A_taxonomy_4__sub_process_structure.md)

### Taxonomy 5: Data and Cross-Pool Communication

- Mode: A
- Models: Lab Diagnostics (v1), Lab Diagnostics (v2)
- Verdict: **unchanged**
- Trace equivalent: True
- Details: 3 operations
- Report: [05_A_taxonomy_5__data_and_cross_pool_communication.md](05_A_taxonomy_5__data_and_cross_pool_communication.md)

### Old vs. new patient registration

- Mode: A
- Models: Registration of old patients, General new patient registration
- Verdict: **semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 12 operations
- Report: [06_A_old_vs__new_patient_registration.md](06_A_old_vs__new_patient_registration.md)

### General vs. corporate new patient registration

- Mode: A
- Models: General new patient registration, Corporate new patient registration
- Verdict: **semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 5 operations
- Report: [07_A_general_vs__corporate_new_patient_registration.md](07_A_general_vs__corporate_new_patient_registration.md)

### General vs. corporate inpatient registration

- Mode: A
- Models: General inpatient registration, Corporate inpatient registration
- Verdict: **semantic_change**
- Trace equivalent: True
- Details: 3 operations
- Report: [08_A_general_vs__corporate_inpatient_registration.md](08_A_general_vs__corporate_inpatient_registration.md)

### General patient cashier vs. down payment

- Mode: A
- Models: General patient cashier, Down payment
- Verdict: **semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 45 operations
- Report: [09_A_general_patient_cashier_vs__down_payment.md](09_A_general_patient_cashier_vs__down_payment.md)

### Patient registration family

- Mode: B
- Models: General new patient registration, Corporate new patient registration, General inpatient registration, Corporate inpatient registration
- Verdict: **semantic_and_behavioral_change, semantic_and_behavioral_change, semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 11 core elements
- Report: [10_B_patient_registration_family.md](10_B_patient_registration_family.md)

### Patient registration evolution chain

- Mode: C
- Models: Registration of old patients, General new patient registration, Corporate new patient registration
- Verdict: **semantic_and_behavioral_change -> semantic_and_behavioral_change**
- Trace equivalent: False
- Details: 0 reverts, oracle consistent=True
- Report: [11_C_patient_registration_evolution_chain.md](11_C_patient_registration_evolution_chain.md)
