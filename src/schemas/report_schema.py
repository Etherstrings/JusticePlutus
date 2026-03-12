"""Minimal schema shim used by the extracted analyzer."""


class AnalysisReportSchema:
    """Compatibility shim for the upstream Pydantic schema."""

    @classmethod
    def model_validate(cls, data):
        """Accept any parsed payload without enforcing a schema."""
        return data
