import tempfile
import unittest
from pathlib import Path

import dendropy

from gtdblib.exception import GtdbLibException
from gtdblib.taxonomy.taxonomy import (check_full_taxonomy, extant_taxa, extant_taxa_for_rank,
                                       fill_missing_ranks, fill_trailing_ranks, read_taxonomy,
                                       read_taxonomy_from_tree, sort_taxa, write_taxonomy)

EMPTY = ['d__', 'p__', 'c__', 'o__', 'f__', 'g__', 's__']


class TestTaxonomy(unittest.TestCase):

    def test_fill_trailing_ranks(self):
        self.assertEqual(fill_trailing_ranks(['d__Bacteria', 'p__Firmicutes']),
                         ['d__Bacteria', 'p__Firmicutes', 'c__', 'o__', 'f__', 'g__', 's__'])

    def test_fill_trailing_ranks_empty(self):
        self.assertEqual(fill_trailing_ranks([]), EMPTY)

    def test_fill_trailing_ranks_does_not_modify_input(self):
        taxa = ['d__Bacteria']
        fill_trailing_ranks(taxa)
        self.assertEqual(taxa, ['d__Bacteria'])

    def test_fill_trailing_ranks_no_prefix(self):
        with self.assertRaises(GtdbLibException):
            fill_trailing_ranks(['d__Bacteria', 'Firmicutes'])

    def test_fill_missing_ranks(self):
        self.assertEqual(fill_missing_ranks(['d__Bacteria', 'c__Bacilli', 'g__Bacillus']),
                         ['d__Bacteria', 'p__', 'c__Bacilli', 'o__', 'f__', 'g__Bacillus', 's__'])

    def test_fill_missing_ranks_repeated_rank(self):
        self.assertEqual(fill_missing_ranks(['d__Bacteria', 'p__A', 'p__B', 'f__C']),
                         ['d__Bacteria', 'p__A', 'p__B', 'c__', 'o__', 'f__C', 'g__', 's__'])

    def test_fill_missing_ranks_non_canonical(self):
        taxa = ['d__Bacteria', 'c__Bacilli', 'p__Firmicutes']
        self.assertEqual(fill_missing_ranks(taxa, warning=False), taxa)

    def test_fill_missing_ranks_no_prefix(self):
        with self.assertRaises(GtdbLibException):
            fill_missing_ranks(['d__Bacteria', 'Firmicutes'])

    def test_check_full_taxonomy(self):
        self.assertTrue(check_full_taxonomy('d__Bacteria;p__;c__;o__;f__;g__;s__'))
        self.assertTrue(check_full_taxonomy('d__Bacteria; p__A; c__B; o__C; f__D; g__E; s__E f'))
        self.assertFalse(check_full_taxonomy('d__Bacteria;p__;c__;o__;f__;g__'))
        self.assertFalse(check_full_taxonomy('d__Bacteria;p__;c__;o__;f__;g__;s__;s__'))
        self.assertFalse(check_full_taxonomy('d__Bacteria;c__;p__;o__;f__;g__;s__'))

    def test_extant_taxa(self):
        taxonomy = {
            'G1': ['d__B', 'p__P1', 'c__', 'o__', 'f__', 'g__', 's__'],
            'G2': ['d__B', 'p__P1', 'c__C1', 'o__', 'f__', 'g__', 's__'],
            'G3': ['d__B', 'p__P2', 'c__C1', 'o__', 'f__', 'g__', 's__'],
        }
        self.assertEqual(extant_taxa_for_rank('phylum', taxonomy), {'p__P1': {'G1', 'G2'}, 'p__P2': {'G3'}})
        self.assertEqual(extant_taxa(taxonomy), {'d__B': {'G1', 'G2', 'G3'},
                                                 'p__P1': {'G1', 'G2'},
                                                 'p__P2': {'G3'},
                                                 'c__C1': {'G2', 'G3'}})
        with self.assertRaises(GtdbLibException):
            extant_taxa_for_rank('kingdom', taxonomy)

    def test_sort_taxa(self):
        taxa = ['g__B', 's__A b', 'd__Z', 'g__A', 'p__Q', 'unranked']
        self.assertEqual(sort_taxa(taxa), ['d__Z', 'p__Q', 'g__A', 'g__B', 's__A b'])
        self.assertEqual(sort_taxa(taxa, reverse=True), ['s__A b', 'g__B', 'g__A', 'p__Q', 'd__Z'])

    def test_write_and_read_taxonomy(self):
        taxonomy = {'G1': ['d__B', 'p__P1', 'c__', 'o__', 'f__', 'g__', 's__'],
                    'G2': ['d__A', 'p__P2', 'c__C', 'o__O', 'f__F', 'g__G', 's__G s']}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'taxonomy.tsv'
            write_taxonomy(taxonomy, str(path))
            self.assertEqual(path.read_text(), 'G1\td__B;p__P1;c__;o__;f__;g__;s__\n'
                                               'G2\td__A;p__P2;c__C;o__O;f__F;g__G;s__G s\n')
            self.assertEqual(read_taxonomy(str(path)), taxonomy)

    def test_read_taxonomy_blank_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'taxonomy.tsv'
            path.write_text('G1\td__B;p__P1\n\nG2\td__A;\n\n')
            self.assertEqual(read_taxonomy(str(path)), {'G1': ['d__B', 'p__P1'], 'G2': ['d__A']})

    def test_read_taxonomy_from_tree_undecorated_leaf(self):
        tree = dendropy.Tree.get(data="((A,B)'d__Bacteria; p__P1',C);", schema='newick')
        taxonomy = read_taxonomy_from_tree(tree)
        self.assertEqual(taxonomy['A'], ['d__Bacteria', 'p__P1', 'c__', 'o__', 'f__', 'g__', 's__'])
        self.assertEqual(taxonomy['C'], EMPTY)

    def test_read_taxonomy_from_tree_labels(self):
        tree = dendropy.Tree.get(
            data="((((A,B)'100:p__P1__c__C1|aux info',C)'90:',D)'95:d__Bacteria;',E)80;",
            schema='newick')
        taxonomy = read_taxonomy_from_tree(tree)
        self.assertEqual(taxonomy['A'], ['d__Bacteria', 'p__P1', 'c__C1', 'o__', 'f__', 'g__', 's__'])
        self.assertEqual(taxonomy['C'], ['d__Bacteria', 'p__', 'c__', 'o__', 'f__', 'g__', 's__'])
        self.assertEqual(taxonomy['E'], EMPTY)

    def test_read_taxonomy_from_tree_species_epithet(self):
        tree = dendropy.Tree.get(
            data="((A,B)'d__B; p__P; c__C; o__O; f__F; g__Gen; s__coli',C);", schema='newick')
        taxonomy = read_taxonomy_from_tree(tree)
        self.assertEqual(taxonomy['A'][6], 's__Gen coli')
        self.assertEqual(taxonomy['B'], taxonomy['A'])
        self.assertIsNot(taxonomy['B'], taxonomy['A'])


if __name__ == '__main__':
    unittest.main()
