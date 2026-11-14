# Scope

| Category | Element | Compared Aspects |
| --- | --- | --- |
| **Event** | Start, Intermediate (catch and throw), End | Event type, event definition (none, message, timer, error, signal, conditional, escalation, compensation, link, terminate), label, lane |
| **Event** | Boundary event| Activity to which the event is attached, interrupting or non-interrupting, event definition|
| **Activity** | Task: user, service, manual, script, send, receive, business rule | Label, task type, lane |
| **Activity** | Sub-process (collapsed or expanded) and Call Activity | Label, sub-process content, called process |
| **Activity** | Loop and multi-instance markers (parallel, sequential) | Presence or absence, marker type |
| **Gateway** | Exclusive (XOR), Inclusive (OR), Parallel (AND), Event-based, Complex | Gateway type, direction (split or join), default flow |
| **Connecting object** | Sequence flow | Source element, target element, condition, default flow |
| **Connecting object** | Message flow | Source and target elements across pools |
| **Swimlane** | Pool (participant), Lane, nested lane | Label, elements belonging to the lane |
| **Data** | Data object, data store, data input and output | Label, connected elements |

# Taxonomy
### bpmndiff Change Taxonomy



| Code and Meaning | Example of Change | How to Detect |
| --- | --- | --- |
| **1. Steps (tasks and events)** |  |  |
| **INSERT_NODE**<br><br>*Add step* | A new task is inserted mid-sequence, as a new XOR branch, or as a new AND branch | An element in the new version has no match in the old version |
| **DELETE_NODE**<br><br>*Delete step* | A task is deleted, then the preceding and succeeding steps are connected | An element in the old version has no match in the new version |
| **RENAME_NODE**<br><br>*Rename step* | A label is replaced with a synonym, paraphrase, or a name with a new meaning | Matched elements have different labels. Also noted whether it is a synonym or if the meaning changed |
| **NODE_TYPE_CHANGE**<br><br>*Change element type* | A user task becomes a service task, or a plain start event becomes a timer event | Matched elements have different task types or event definitions |
| **MARKER_CHANGE**<br><br>*Change marker* | A plain task is given a loop or multi-instance marker, or vice versa | Matched elements have different markers |
| **BOUNDARY_CHANGE**<br><br>*Change boundary event* | A boundary timer is moved to another activity, or interrupting is changed to non-interrupting | Matched boundary events have a different attached activity or interrupting property |
| **2. Actors (lanes and pools)** |  |  |
| **MOVE_LANE**<br><br>*Change actor* | A task is moved to another lane or another pool | Matched elements belong to different lanes |
| **RENAME_LANE**<br><br>*Rename lane or pool* | Lane "Cashier" becomes "Cashier Officer" | Matched lanes have different labels |
| **INSERT_LANE**<br><br>**DELETE_LANE**<br><br>*Add or delete actor* | Lane "Verifier" is added, or an unused lane is deleted | A lane has no match in one of the versions |
| **3. Sequence, flow, and branching** |  |  |
| **REORDER**<br><br>*Change order* | A task is moved to another position, or two sequential tasks are swapped | Element positions in the flow change, after added and deleted elements are excluded from comparison |
| **GATEWAY_TYPE_CHANGE**<br><br>*Change branching type* | XOR becomes AND, AND becomes OR, or XOR becomes event-based | Matched gateways have different types |
| **INSERT_FLOW**<br><br>**DELETE_FLOW**<br><br>*Add or delete path* | A new loop path is added, or a shortcut path is deleted | A sequence flow between two matched elements exists in only one version and is not explained by other changes |
| **FLOW_CONDITION_CHANGE**<br><br>*Change flow condition* | Condition "amount above 1 million" is changed, or the default flow is moved to another branch | Matched flows have different conditions or default flow statuses |
| **PARALLELIZE**<br><br>**SEQUENTIALIZE**<br><br>*Make parallel or sequential* | Two sequential tasks are enclosed by AND gateways to run in parallel, or vice versa | Matched elements that were previously sequential are now on different branches of an AND gateway, or vice versa |
| **4. Sub-process structure** |  |  |
| **EXTRACT_SUBPROCESS**<br><br>**INLINE_SUBPROCESS**<br><br>*Wrap or unwrap sub-process* | Three verification tasks are wrapped into a single sub-process, or a sub-process is unpacked back into plain tasks | Matched elements move into a new sub-process, or exit from a deleted sub-process |
| **5. Data and cross-pool communication** |  |  |
| **MESSAGE_FLOW_CHANGE**<br><br>*Change cross-pool communication* | A message flow from the Patient pool to the Hospital pool is added, deleted, or moved | A message flow between matched elements exists in only one version, or its source and target differ |
| **DATA_CHANGE**<br><br>*Change data* | Data store "Patient" is added, or a task no longer reads a specific data object | An unmatched data object or data store, or a different data association |