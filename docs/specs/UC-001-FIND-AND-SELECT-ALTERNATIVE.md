# UC-001-FIND-AND-SELECT-ALTERNATIVE

Incomplete draft — pending definition and owner review.

## Intent

Help a user find and select a practical alternative to a product,
service, purchase, or everyday habit or behaviour by comparing
financial and environmental/resource implications. Build reusable
Resolena knowledge from requests, evidence-backed results and
explicit selections.

## Actors

Primary: A user seeking an alternative, without needing an account.

Secondary: An external research service, if configured and approved,
used only when existing knowledge is insufficient and only through
minimized, non-identifying queries.

The knowledge base and database are internal system components,
not external actors.

## Preconditions

- The user can access the Alternative Finder.
- Resolena-controlled persistence is available.
- Existing knowledge may be empty; previous requests or selections
  are not required.
- External research must satisfy the approved privacy boundary
  before it can be used.

## Flow

1. Submit: The user submits a text description of a product, service,
   purchase, habit or behaviour, including their goal and any relevant
   constraints.

2. Interpret: The system validates and normalizes the request,
   identifying its category, current choice, goal and stated
   constraints. It does not invent missing facts.

3. Retrieve: The system searches existing Resolena knowledge for
   relevant alternatives and supporting evidence.

4. Assess: The system assesses relevance, evidence quality and
   freshness to determine whether existing knowledge is sufficient.

5. Research when needed: If knowledge is insufficient, the system
   uses an approved research integration with minimized,
   non-identifying queries. Sufficient existing knowledge is reused
   without new research.

6. Prepare comparison: The system prepares a small set of alternatives
   with financial and environmental/resource information, explanations,
   evidence references and confidence/validation labels. Unknown values
   and assumptions are identified explicitly.

7. Persist and present: The system persists the original request,
   normalized interpretation, alternatives prepared for display and
   their supporting evidence, then presents the comparison. Newly
   acquired knowledge becomes available for future retrieval, subject
   to the same quality checks.

   Search results are saved before selection. If the user leaves without
   choosing, the saved request and results remain; no selection is
   inferred.

8. Select: The user explicitly selects one of the displayed
   alternatives. The system stores the selection against that request
   and confirms it was saved.

9. Preserve evidence integrity: The selection is available as a
   relevance signal for future requests. It does not automatically
   change factual confidence or validation status.

## Errors

Pending definition and owner review.

## Acceptance

Pending definition and owner review.

## Tests

Pending definition and owner review.
