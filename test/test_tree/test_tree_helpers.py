import tempfile
import unittest
from pathlib import Path

import dendropy

from gtdblib import log
from gtdblib.tree.convert_accession import convert_tree_accessions_to_canonical
from gtdblib.tree.get_node_to_desc_taxa import get_tree_node_to_desc_taxa
from gtdblib.tree.get_unique_mrca_for_internal_nodes import get_tree_unique_mrca_for_internal_nodes


def _tree():
    return dendropy.Tree.get(data='(((A,B)n1,C)n2,(D,(E,F)n3)n4)root;', schema='newick')


def _by_label(d):
    return {n.label: v for n, v in d.items() if n.label}


class TestTreeHelpers(unittest.TestCase):

    def test_get_tree_node_to_desc_taxa(self):
        tree = _tree()
        desc = get_tree_node_to_desc_taxa(tree)
        self.assertEqual(_by_label(desc), {
            'n1': {'A', 'B'},
            'n2': {'A', 'B', 'C'},
            'n3': {'E', 'F'},
            'n4': {'D', 'E', 'F'},
            'root': {'A', 'B', 'C', 'D', 'E', 'F'},
        })
        self.assertEqual(desc[tree.find_node_with_taxon_label('A')], {'A'})
        self.assertTrue(all(isinstance(v, frozenset) for v in desc.values()))

    def test_get_tree_unique_mrca_for_internal_nodes(self):
        tree = _tree()
        mrca = get_tree_unique_mrca_for_internal_nodes(tree)
        self.assertEqual(_by_label(mrca), {
            'n1': ('A', 'B'),
            'n2': ('A', 'C'),
            'n3': ('E', 'F'),
            'n4': ('D', 'E'),
            'root': ('A', 'D'),
        })
        for node, (t1, t2) in mrca.items():
            self.assertIs(tree.mrca(taxon_labels=[t1, t2]), node)

    def test_convert_accessions_duplicate_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            path_in = Path(tmp) / 'in.tree'
            path_out = Path(tmp) / 'out.tree'
            path_in.write_text('((GB_GCA_000000001.1,RS_GCF_000000001.1),GCF_000000002.1);')

            with self.assertLogs(log, level='WARNING') as cm:
                convert_tree_accessions_to_canonical(path_in, path_out)

            self.assertEqual(path_out.read_text().strip(), '((G000000001,G000000001),G000000002);')

        warnings = [r.getMessage() for r in cm.records if r.levelname == 'WARNING']
        self.assertEqual(warnings, ['Leaf node RS_GCF_000000001.1 -> G000000001 is a duplicate '
                                    'of GB_GCA_000000001.1'])


if __name__ == '__main__':
    unittest.main()
