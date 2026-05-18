class Finding:

    def __init__(self, finding_id, severity):
        self.finding_id = finding_id
        self.severity = severity

    def to_dict(self):

        return {
            "id": self.finding_id,
            "severity": self.severity
        }
