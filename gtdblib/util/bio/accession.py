import re

RE_CANONICAL = re.compile(r'^(?:GB_)?(?:RS_)?(?:GCF_)?(?:GCA_)?(\d{9})\.\d')


def canonical_gid(gid: str) -> str:
    """Get canonical form of NCBI genome accession.

    Example:
        G005435135 -> G005435135
        GCF_005435135.1 -> G005435135
        GCF_005435135.1_ASM543513v1_genomic -> G005435135
        RS_GCF_005435135.1 -> G005435135
        GB_GCA_005435135.1 -> G005435135
    """

    match = RE_CANONICAL.match(gid)
    if match:
        return f'G{match[1]}'
    else:
        return gid
