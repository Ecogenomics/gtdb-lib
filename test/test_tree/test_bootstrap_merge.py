import random
import re
import tempfile
import unittest
from pathlib import Path

import dendropy

from gtdblib.exception import GtdbLibException
from gtdblib.tree.bootstrap_merge import bootstrap_merge_replicates


def _random_topology(taxa, rng):
    """Random rooted binary topology as nested tuples."""
    nodes = list(taxa)
    while len(nodes) > 2:
        x = nodes.pop(rng.randrange(len(nodes)))
        y = nodes.pop(rng.randrange(len(nodes)))
        nodes.append((x, y))
    return tuple(nodes)


def _shuffle(t, rng):
    if isinstance(t, str):
        return t
    kids = [_shuffle(c, rng) for c in t]
    rng.shuffle(kids)
    return tuple(kids)


def _prune(t, keep):
    if isinstance(t, str):
        return t if t in keep else None
    kids = [k for k in (_prune(c, keep) for c in t) if k is not None]
    if not kids:
        return None
    return kids[0] if len(kids) == 1 else tuple(kids)


def _to_newick(t, labels=None):
    def rec(n):
        if isinstance(n, str):
            return f'{n}:0.1'
        lab = labels(n) if labels else ''
        return '(' + ','.join(rec(c) for c in n) + ')' + lab + ':0.1'
    return rec(t)[:-4] + ';'


def _leaves(t):
    return frozenset([t]) if isinstance(t, str) else frozenset().union(*(_leaves(c) for c in t))


def _clades(t, out=None):
    out = [] if out is None else out
    if not isinstance(t, str):
        out.append(_leaves(t))
        for c in t:
            _clades(c, out)
    return out


def _reference_support(ref, replicates):
    """Brute-force support for each clade of `ref` (keyed by its taxa)."""
    ref_taxa = _leaves(ref)
    rep_info = []
    for rep in replicates:
        rep_taxa = _leaves(rep)
        common = rep_taxa & ref_taxa
        bps = set()
        for clade in _clades(rep):
            a = clade & common
            b = common - a
            if len(a) >= 2 and len(b) >= 2:
                bps.add(frozenset([a, b]))
        rep_info.append((common, bps))

    support = {}
    for clade in _clades(ref):
        if clade == ref_taxa:
            continue
        n_sup = n_counted = 0
        for common, bps in rep_info:
            a = clade & common
            b = common - a
            if len(a) < 2 or len(b) < 2:
                continue
            n_counted += 1
            n_sup += frozenset([a, b]) in bps
        support[clade] = (n_sup * 100 // n_counted) if n_counted else None
    return support


def _read_labels(path):
    """Map the taxa below each internal node to its label (root keyed by 'ROOT')."""
    tree = dendropy.Tree.get_from_path(str(path), schema='newick', preserve_underscores=True,
                                       rooting='force-rooted')
    out = {}
    for node in tree.postorder_internal_node_iter():
        taxa = frozenset(leaf.taxon.label for leaf in node.leaf_iter())
        out['ROOT' if node is tree.seed_node else taxa] = node.label
    return out


class TestTreeBootstrapMerge(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, text):
        path = self.tmp / name
        path.write_text(text + '\n')
        return path

    def _run(self, ref_text, rep_texts, cpus=1):
        ref = self._write('ref.tree', ref_text)
        reps = [self._write(f'rep{i}.tree', t) for i, t in enumerate(rep_texts)]
        out = self.tmp / 'out.tree'
        bootstrap_merge_replicates(ref, out, reps, cpus=cpus)
        return out.read_text().strip()

    def test_simple(self):
        # 3 of 4 replicates support AB, ABC|DEF, and DEF; 2 of 4 support DE
        out = self._run('(((A,B),C),((D,E),F));', [
            '((A,B),(C,(D,(E,F))));',
            '(((B,A),C),(F,(D,E)));',
            '((C,(A,B)),((E,D),F));',
            '((A,D),((B,C),(E,F)));',
        ])
        self.assertEqual(out, '(((A,B)75,C)75,((D,E)50,F)75);')

    def test_root_label_unchanged(self):
        out = self._run("[&R] ((A,B)'99',(C,D)'old')'root label';", ['((A,B),(C,D));'])
        self.assertEqual(out, "[&R] ((A,B)'100',(C,D)'100:old')'root label';")

    def test_taxon_labels_and_format_preserved(self):
        ref = ("((('A 1':0.1,B_2:0.2)'80:p__X':0.3,C:0.4)'g__Y|aux':0.5,"
               "(D:0.6,E:0.7)'p__Z; c__W':0.8,F:0.9);")
        rep = "((('A 1',B_2),C),(D,E),F);"
        out = self._run(ref, [rep, rep])
        self.assertEqual(out, ("((('A 1':0.1,B_2:0.2)'100:p__X':0.3,C:0.4)'100:g__Y|aux':0.5,"
                               "(D:0.6,E:0.7)'100:p__Z; c__W':0.8,F:0.9);"))

    def test_trivial_edge_has_no_support(self):
        # the clade (B,C,D) is the complement of A, so it is not a bipartition
        # and is left unlabelled, while (C,D) is the bipartition CD|AB
        out = self._run('(A,(B,(C,D)));', ['(A,(B,(C,D)));'])
        self.assertEqual(out, '(A,(B,(C,D)100));')

    def test_matches_brute_force(self):
        rng = random.Random(42)
        taxa = [f'G{i:03d}' for i in range(40)]
        for trial in range(5):
            ref = _random_topology(taxa, rng)
            reps = []
            for i in range(12):
                if i % 3 == 0:
                    reps.append(_random_topology(taxa, rng))
                elif i % 3 == 1:
                    reps.append(_shuffle(ref, rng))
                else:
                    # jackknifed taxa: a random subset of the input taxa
                    keep = set(rng.sample(taxa, 30))
                    src = ref if rng.random() < 0.5 else _random_topology(taxa, rng)
                    reps.append(_prune(_shuffle(src, rng), keep))

            ref_path = self._write('ref.tree', _to_newick(ref))
            rep_paths = [self._write(f'rep{i}.tree', _to_newick(r)) for i, r in enumerate(reps)]
            out = self.tmp / 'out.tree'
            bootstrap_merge_replicates(ref_path, out, rep_paths, cpus=1)

            expected = _reference_support(ref, reps)
            labels = _read_labels(out)
            for clade, exp in expected.items():
                got = labels[clade]
                self.assertEqual(None if got is None else int(got), exp, f'trial {trial}, clade {sorted(clade)}')
            self.assertIsNone(labels['ROOT'])

    def test_replicate_with_extra_taxa(self):
        # X is not in the input tree and must be ignored
        out = self._run('((A,B),(C,D),E);', ['(((A,B),X),(C,D),E);', '((A,C),(B,D),(E,X));'])
        self.assertEqual(out, '((A,B)50,(C,D)50,E);')

    def test_multiple_cpus_match_single(self):
        rng = random.Random(7)
        taxa = [f't{i}' for i in range(60)]
        ref = _to_newick(_random_topology(taxa, rng))
        reps = [_to_newick(_random_topology(taxa, rng) if i % 2 else _shuffle(_random_topology(taxa, rng), rng))
                for i in range(8)]
        reps[0] = ref
        self.assertEqual(self._run(ref, reps, cpus=1), self._run(ref, reps, cpus=3))

    def test_duplicate_taxa(self):
        with self.assertRaises(GtdbLibException):
            self._run('((A,B),(A,C));', ['((A,B),(C,D));'])

    def test_invalid_arguments(self):
        ref = self._write('ref.tree', '((A,B),(C,D));')
        with self.assertRaises(ValueError):
            bootstrap_merge_replicates(ref, self.tmp / 'out.tree', [])
        with self.assertRaises(ValueError):
            bootstrap_merge_replicates(ref, self.tmp / 'out.tree', str(ref))


if __name__ == '__main__':
    unittest.main()
