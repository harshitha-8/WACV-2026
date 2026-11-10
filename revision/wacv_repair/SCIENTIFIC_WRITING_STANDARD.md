# Scientific Writing and Claim Standard

## Desired voice

Write as a precise computer-vision systems paper grounded in a real precision-
agriculture decision. The prose should be direct, falsifiable, and technically
specific. Importance comes from the problem formulation, experimental control,
and insight, not promotional adjectives.

## Sentence-level rules

- One scientific claim per sentence where possible.
- Use active verbs: defines, measures, compares, retains, reduces, fails.
- State the unit and condition with every quantitative claim.
- Distinguish observation, inference, hypothesis, and limitation.
- Replace "novel," "reliable," "robust," "efficient," and "significant" with a
  metric or controlled comparison unless the term is formally established.
- Never use drafting instructions, future-tense result promises, or `TBD` in a
  submission build.

## Claim grammar

Preferred:

> At K=8 on the held-out source split, policy A changed source-level metric X by
> delta relative to policy B (source-clustered 95% interval [L, U]).

Avoid:

> Policy A intelligently and significantly improves robust monitoring.

## Agricultural boundaries

Allowed claims:

- inventory-oriented plant presence and count;
- canopy-density or annotated-coverage categories when defined and supported;
- evidence sufficiency and human-review routing; and
- performance under the observed Magnolia/Azalea acquisition domains.

Disallowed without new labels:

- plant health, stress, disease, mortality, quality, treatment need, or yield;
- agronomic recommendations; and
- universal nursery generalization.

## How to express the contribution

Do not call the VLM itself the contribution. The contribution is the controlled
allocation and acceptance of expensive multimodal evidence under source-level
shift. The detector, selector, VLM, gate, and reducer form one evaluated system.

## How to report mixed results

Mixed results are an insight, not a weakness to hide. If count top-K maximizes
foreground recall while exploit--explore improves risk ranking or negative
evidence, describe a Pareto frontier and identify which operating condition
prefers each policy.

## Section-level writing gate

For every subsection, answer:

1. What question is being tested?
2. What is held constant?
3. What changes?
4. What is the unit of analysis?
5. What result answers the question?
6. What conclusion is justified?
7. What conclusion is not justified?

If any answer is missing, the subsection is not ready.
