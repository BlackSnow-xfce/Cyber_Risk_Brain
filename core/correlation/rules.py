def critical_attack_surface(context):

    if (
        context.internet_facing
        and context.critical_count > 0
        and context.exploit_count > 0
    ):

        return [{
            "type": "critical_attack_surface",
            "reason": (
                "Internet-facing asset with an exploitable "
                "critical vulnerability."
            )
        }]

    return []


def internet_exposure(context):

    if context.internet_facing:

        return [{
            "type": "internet_exposure",
            "reason": "Asset is internet-facing"
        }]

    return []


def critical_vulnerability(context):

    if context.critical_count > 0:

        return [{
            "type": "critical_vulnerability",
            "reason": "Critical vulnerability detected"
        }]

    return []


def public_exploit(context):

    if context.exploit_count > 0:

        return [{
            "type": "public_exploit",
            "reason": "Public exploit available"
        }]

    return []


def high_cvss(context):

    if context.max_cvss >= 9.0:

        return [{
            "type": "high_cvss",
            "reason": "CVSS >= 9.0"
        }]

    return []


def medium_vulnerability(context):

    if context.medium_count > 0:

        return [{
            "type": "medium_vulnerability",
            "reason": "Medium vulnerability detected"
        }]

    return []


def crown_jewel(context):

    if context.metadata.crown_jewel:

        return [{
            "type": "crown_jewel",
            "reason": "Asset is classified as a Crown Jewel."
        }]

    return []


RULES = [
    critical_attack_surface,
    internet_exposure,
    critical_vulnerability,
    public_exploit,
    high_cvss,
    medium_vulnerability,
    crown_jewel
]
