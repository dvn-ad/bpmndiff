==============================================================================
 bpmndiff | Mode A | pairwise process comparison
==============================================================================
 Reference : Diagram 2.bpmn  (bpmn, Diagram 2.bpmn)
             18 nodes, 20 flows
 Variant   : Down payment  (bpmn, Diagram 3.bpmn)
             18 nodes, 20 flows

 Alignment : 10 identical, 2 synonym, 5 meaning-changed, 1 deleted, 1 inserted

 Edit script (11 operations)
------------------------------------------------------------------------------
  DELETE               Invisible Task
  INSERT               Displays the message data not found
  RENAME               "Enters Down Payment information" -> "Enters the receipt number"
  RENAME               "Saves the Down Payment information" -> "Prints the receipt"
  RENAME               "Displays patient information" -> "Displays payment information"
  RENAME               "Wants to make a Down Payment transaction" -> "Wants to make Reprint hospitalization receipts"
  RENAME               "Displays Down Payment transaction form" -> "Displays the Reprint hospitalization receipts form"
  RENAME               "Searches for patients by register number" -> "Searches for the receipt number"
  RENAME               "Selects a save button" -> "Selects a print button"
  INSERT_FLOW          <exclusive gateway (XOR)> -> Displays the message data not found
  INSERT_FLOW          Displays the message data not found -> <exclusive gateway (XOR)>

 Behaviour
------------------------------------------------------------------------------
  Trace equivalence      : NOT EQUIVALENT
  Method                 : trace_equivalence (tau-closure + subset construction)
  Counterexample [variant_only] : Wants to make a Down Payment transaction -> Displays Down Payment transaction form -> Enters Down Payment information -> Searches for patients by register number -> Displays the message data not found -> Invisible Task -> Selects a save button -> Invisible Task
     only this model can execute the differing task and still complete
  Branching bisimulation : NOT EQUIVALENT (initial states are separated by partition refinement)
  Reference trace sample :
     Wants to make a Down Payment transaction -> Displays Down Payment transaction form -> Enters Down Payment information -> Searches for patients by register number -> Displays patient information -> Invisible Task -> Selects a save button -> Invisible Task
     Wants to make a Down Payment transaction -> Displays Down Payment transaction form -> Enters Down Payment information -> Searches for patients by register number -> Displays patient information -> Invisible Task -> Selects a save button -> Saves the Down Payment information
     Wants to make a Down Payment transaction -> Displays Down Payment transaction form -> Enters Down Payment information -> Searches for patients by register number -> Invisible Task -> Invisible Task -> Selects a save button -> Invisible Task

 SESE fragments: 30 region(s), 3 affected
------------------------------------------------------------------------------
  R03 [3 nodes] EQUIVALENT
  R17 [11 nodes] EQUIVALENT
  R22 [14 nodes] SKIPPED - fragment has no entry point

 Fusion verdict
------------------------------------------------------------------------------
  Overall     : semantic_and_behavioral_change
  Element mix : {'behavioral_change': 2, 'semantic_change': 5, 'unchanged': 10, 'structural_change': 2}