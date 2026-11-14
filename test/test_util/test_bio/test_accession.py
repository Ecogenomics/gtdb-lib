import unittest

from gtdblib.util.bio.accession import canonical_gid
from gtdblib.util.bio.newick import parse_label


class TestAccession(unittest.TestCase):

    def test_canonical_gid(self):
        self.assertEqual(canonical_gid('NC_000913.3'), 'NC_000913.3')
        self.assertEqual(canonical_gid('G005435135'), 'G005435135')

        self.assertEqual(canonical_gid('GCA_005435135.1'), 'G005435135')
        self.assertEqual(canonical_gid('GCF_005435135.1'), 'G005435135')

        self.assertEqual(canonical_gid('GB_GCA_005435135.1'), 'G005435135')
        self.assertEqual(canonical_gid('RS_GCF_005435135.1'), 'G005435135')

        self.assertEqual(canonical_gid('GCF_005435135.1_ASM543513v1_genomic'), 'G005435135')
        self.assertEqual(canonical_gid('GCA_005435135.1_ASM543513v1_genomic'), 'G005435135')

        self.assertEqual(canonical_gid('GB_GCA_005435135.1_ASM543513v1_genomic'), 'G005435135')
        self.assertEqual(canonical_gid('RS_GCF_005435135.1_ASM543513v1_genomic'), 'G005435135')


class TestNewick(unittest.TestCase):

    def test_parse_label(self):
        self.assertEqual(parse_label('100:d__Bacteria'), (100.0, 'd__Bacteria', None))
        self.assertEqual(parse_label('100:d__Bacteria|aux'), (100.0, 'd__Bacteria', 'aux'))
        self.assertEqual(parse_label('100:a:b'), (100.0, 'a:b', None))
