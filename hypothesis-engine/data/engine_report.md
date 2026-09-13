# Hypothesis engine run report

Run at: 2026-09-10T10:26:00+00:00

## Stage counts

- **topics**: 8
- **raw_findings**: 175
- **new_findings**: 50
- **duplicates_skipped**: 125
- **claims_staked**: 50
- **routed_to_unknown**: 0
- **test_pass**: 265
- **test_fail**: 38
- **test_untested**: 90
- **modify_reformulated**: 12
- **modify_escape_hatched**: 1
- **hidden_variable_suggestions**: [{'topic': 'deployment-aware compression metrics', 'suggested_variable': 'hidden:deployment-aware compression metrics vs exogenous:findings_rate', 'pearson_r': -0.9592, 'mean_abs_residual': 0.2533, 'confidence': 0.95, 'at': '2026-09-10T10:26:00+00:00', 'type': 'hidden_variable_suggestion'}]
- **hypothesis_files**: 8
- **new_hypotheses**: ['compression composition and ordering', 'hidden variable detection / causal discovery from residuals', 'activation-aware quantization', 'world models and curiosity-driven learning', 'structured sparsity and hardware-matched pruning', 'calibration and falsifiability of LLM agents', 'deployment-aware compression metrics']
- **total_claims_in_tree**: 349

## New hypotheses
NEW HYPOTHESIS

- compression composition and ordering
- hidden variable detection / causal discovery from residuals
- activation-aware quantization
- world models and curiosity-driven learning
- structured sparsity and hardware-matched pruning
- calibration and falsifiability of LLM agents
- deployment-aware compression metrics

## Top hidden-variable suspects

- hidden:deployment-aware compression metrics vs exogenous:findings_rate (r=-0.9592)
