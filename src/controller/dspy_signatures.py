"""DSPy signatures for SFDR extraction tasks."""

import dspy


class ClassifyArticle(dspy.Signature):
    """Classify which SFDR article (6, 8, or 9) a fund follows."""

    context = dspy.InputField(desc="Text from fund documentation")
    article = dspy.OutputField(desc="SFDR article: '6', '8', or '9'")
    confidence = dspy.OutputField(desc="Confidence score 0.0-1.0")
    reasoning = dspy.OutputField(desc="Brief explanation of classification")


class ExtractDefinition(dspy.Signature):
    """Extract sustainable investment definition from fund documents."""

    context = dspy.InputField(desc="Relevant text sections about sustainable investment")
    definition_present = dspy.OutputField(desc="true if definition found, false otherwise")
    definition_text = dspy.OutputField(desc="The sustainable investment definition text")
    page_number = dspy.OutputField(desc="Page number where definition appears")
    confidence = dspy.OutputField(desc="Confidence score 0.0-1.0")


class ExtractDNSH(dspy.Signature):
    """Extract Do No Significant Harm (DNSH) information."""

    context = dspy.InputField(desc="Relevant text sections about DNSH")
    dnsh_present = dspy.OutputField(desc="true if DNSH mentioned, false otherwise")
    coverage = dspy.OutputField(desc="Coverage level: none, partial, or full")
    page_number = dspy.OutputField(desc="Page number where DNSH appears")
    confidence = dspy.OutputField(desc="Confidence score 0.0-1.0")


class ExtractPAI(dspy.Signature):
    """Extract Principal Adverse Impact (PAI) information."""

    context = dspy.InputField(desc="Relevant text sections about PAI")
    mandatory_coverage_ratio = dspy.OutputField(desc="Ratio of mandatory PAIs covered (0.0-1.0)")
    page_number = dspy.OutputField(desc="Page number where PAI information appears")
    confidence = dspy.OutputField(desc="Confidence score 0.0-1.0")
