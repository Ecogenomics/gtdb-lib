"""Non-parametric bootstrap support from replicate trees.

Splits are compared using XOR hashing: every taxon is assigned a random
128-bit value and the hash of a split is the XOR of the values of the taxa
on one side of it, normalised as ``min(h, h ^ h_all)`` so both sides of a
bipartition give the same value. This makes the cost of each replicate linear
in the number of taxa, so trees with hundreds of thousands of taxa can be
processed in seconds per replicate.

Support for an edge in the input tree is the percentage of replicates that
contain the same bipartition, after restricting both trees to the taxa they
have in common. Replicates in which the edge is trivial after this
restriction (fewer than two taxa on either side) are excluded from that
edge's denominator, so replicates containing a subset of the taxa (e.g.
jackknifed taxa) are handled correctly.

The text of the input tree (rooting, branch lengths, quoting, comments) is
preserved. Only internal node labels are changed: the support value is
combined with any existing taxon label as ``support:taxon`` (see
:func:`gtdblib.util.bio.newick.create_label`), replacing any existing
support value. The label of the root node is left unchanged as it does not
correspond to an edge. If the root is bifurcating, both of its children
represent the same bipartition and receive the same support value.
"""

import multiprocessing as mp
import os
import random
import re
from math import floor
from typing import Collection, Dict, List, Optional, Tuple, Union

import numpy as np
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn

from gtdblib import log
from gtdblib.exception import GtdbLibException
from gtdblib.util.bio.newick import parse_label, create_label

# Tokens in a Newick string: structure characters, quoted labels, comments,
# and unquoted labels (which stop at structure characters and ':').
_TOKEN = re.compile(r"\s*(\(|\)|,|;|'(?:[^']|'')*'|\[[^\]]*\]|[^(),;:'\[\s][^(),;:'\[]*)")
_LENGTH = re.compile(r"\s*:\s*[^(),;\[]*")
_COMMENT = re.compile(r"\s*\[[^\]]*\]")

# Characters that require a label to be quoted in Newick format.
_NEEDS_QUOTES = re.compile(r"[\s:;,()\[\]']")

PathLike = Union[str, os.PathLike]


class _NewickTree:
    """Minimal Newick representation used for split hashing.

    Nodes are numbered in postorder, so children always precede their parent.
    """

    __slots__ = ('text', 'children', 'leaf_name', 'label_span', 'root')

    def __init__(self, text: str, source: str = '<string>'):
        self.text = text
        self.children: List[List[int]] = []
        self.leaf_name: List[Optional[str]] = []
        # internal node -> (start, end) of its label in text
        self.label_span: Dict[int, Tuple[int, int]] = {}
        self.root: Optional[int] = None
        self._parse(source)

    def _skip(self, pos: int) -> int:
        """Skip comments and a branch length following a node."""
        while True:
            m = _COMMENT.match(self.text, pos)
            if m:
                pos = m.end()
                continue
            m = _LENGTH.match(self.text, pos)
            if m:
                pos = m.end()
                continue
            return pos

    def _parse(self, source: str):
        text = self.text
        stack: List[List[int]] = []
        pos = 0
        while True:
            m = _TOKEN.match(text, pos)
            if not m:
                if text[pos:].strip():
                    raise GtdbLibException(f'Unable to parse Newick tree {source} at position {pos}.')
                break
            tok = m.group(1)
            pos = m.end()

            if tok[0] == '[' or tok == ',':
                continue
            elif tok == '(':
                stack.append([])
            elif tok == ')':
                if not stack:
                    raise GtdbLibException(f'Unbalanced parentheses in Newick tree {source}.')
                idx = len(self.children)
                self.children.append(stack.pop())
                self.leaf_name.append(None)

                # optional label directly after the closing parenthesis
                m_lab = _TOKEN.match(text, pos)
                if m_lab and m_lab.group(1)[0] not in '(),;[':
                    self.label_span[idx] = (m_lab.start(1), m_lab.end(1))
                    pos = m_lab.end()
                else:
                    self.label_span[idx] = (pos, pos)
                pos = self._skip(pos)

                if stack:
                    stack[-1].append(idx)
                elif self.root is None:
                    self.root = idx
                else:
                    raise GtdbLibException(f'Newick tree {source} has multiple roots.')
            elif tok == ';':
                break
            else:
                if not stack:
                    raise GtdbLibException(f'Unexpected label outside of a clade in Newick tree {source}.')
                idx = len(self.children)
                self.children.append([])
                self.leaf_name.append(_unquote(tok))
                stack[-1].append(idx)
                pos = self._skip(pos)

        if stack or self.root is None:
            raise GtdbLibException(f'Invalid or empty Newick tree: {source}')

        names = [x for x in self.leaf_name if x is not None]
        if len(names) != len(set(names)):
            seen = set()
            dup = next(x for x in names if x in seen or seen.add(x))
            raise GtdbLibException(f'Taxon {dup} occurs multiple times in Newick tree {source}.')

    @classmethod
    def from_path(cls, path: PathLike) -> '_NewickTree':
        with open(path) as f:
            return cls(f.read(), str(path))

    def taxa(self) -> List[str]:
        return [x for x in self.leaf_name if x is not None]


def _unquote(label: str) -> str:
    label = label.strip()
    if len(label) >= 2 and label[0] == "'" and label[-1] == "'":
        return label[1:-1].replace("''", "'")
    return label


def _quote(label: str, force: bool) -> str:
    if label and (force or _NEEDS_QUOTES.search(label)):
        return "'" + label.replace("'", "''") + "'"
    return label


def _taxon_hashes(taxa: Collection[str]) -> Dict[str, int]:
    """Assign a deterministic random 128-bit value to each taxon."""
    rng = random.Random(0)
    return {taxon: rng.getrandbits(128) for taxon in sorted(taxa)}


def _split_hashes(tree: _NewickTree, hashes: Dict[str, int], keep: Optional[frozenset] = None):
    """Hash and taxon count of the split below each node.

    Taxa not in `hashes` (or not in `keep`, if given) are ignored.
    """
    n_nodes = len(tree.children)
    h = [0] * n_nodes
    c = [0] * n_nodes
    for i, kids in enumerate(tree.children):
        if kids:
            hv = 0
            cv = 0
            for k in kids:
                hv ^= h[k]
                cv += c[k]
            h[i] = hv
            c[i] = cv
        else:
            name = tree.leaf_name[i]
            if name in hashes and (keep is None or name in keep):
                h[i] = hashes[name]
                c[i] = 1
    return h, c


# State shared with worker processes (set by _init_worker).
_WORKER = {}


def _init_worker(ref_tree: _NewickTree, hashes: Dict[str, int]):
    _WORKER['ref'] = ref_tree
    _WORKER['hashes'] = hashes


def _score_replicate(rep_path: PathLike) -> Tuple[bytes, bytes]:
    """Determine which edges of the input tree are present in a replicate.

    :return: Two byte arrays over the nodes of the input tree, indicating if the
        node's split is supported by the replicate, and if the split is non-trivial
        in the replicate (i.e. counts towards the denominator).
    """
    ref: _NewickTree = _WORKER['ref']
    hashes: Dict[str, int] = _WORKER['hashes']

    rep = _NewickTree.from_path(rep_path)
    common = frozenset(t for t in rep.taxa() if t in hashes)
    n_common = len(common)

    # non-trivial splits in the replicate, restricted to the common taxa
    h_all = 0
    for taxon in common:
        h_all ^= hashes[taxon]
    rep_h, rep_c = _split_hashes(rep, hashes)
    rep_splits = set()
    for i, kids in enumerate(rep.children):
        if kids and 2 <= rep_c[i] <= n_common - 2:
            rep_splits.add(min(rep_h[i], rep_h[i] ^ h_all))

    # splits in the input tree, restricted to the common taxa
    ref_h, ref_c = _split_hashes(ref, hashes, common)
    supported = bytearray(len(ref.children))
    counted = bytearray(len(ref.children))
    for i, kids in enumerate(ref.children):
        if kids and i != ref.root and 2 <= ref_c[i] <= n_common - 2:
            counted[i] = 1
            if min(ref_h[i], ref_h[i] ^ h_all) in rep_splits:
                supported[i] = 1

    return bytes(supported), bytes(counted)


def _support_label(raw_label: str, support: Optional[int]) -> str:
    """Combine a support value with an existing internal node label."""

    was_quoted = raw_label.startswith("'")
    label = _unquote(raw_label)
    try:
        _old_support, taxon, aux_info = parse_label(label)
    except ValueError:
        # label contains ':' but does not start with a support value
        taxon, aux_info = label, None

    return _quote(create_label(support, taxon, aux_info), was_quoted)


def bootstrap_merge_replicates(
        input_tree: PathLike,
        output_tree: PathLike,
        replicate_trees: Collection[PathLike],
        cpus: int = 1
):
    """Calculates non-parametric bootstrap support for the edges of a tree and
    writes them as internal node labels.

    :param input_tree: The tree to merge the bootstraps to.
    :param output_tree: The path to write the tree to.
    :param replicate_trees: The trees to calculate the bootstraps from. These may
        contain a subset (or superset) of the taxa in the input tree.
    :param cpus: The number of processes to use.
    """

    # Validate arguments
    if isinstance(replicate_trees, (str, os.PathLike)) or not isinstance(replicate_trees, Collection):
        raise ValueError('Replicate trees must be a collection of paths.')
    if len(replicate_trees) == 0:
        raise ValueError('At least one replicate tree must be provided.')
    if cpus is None or not isinstance(cpus, int) or cpus < 1:
        cpus = 1

    ref = _NewickTree.from_path(input_tree)
    hashes = _taxon_hashes(ref.taxa())

    n_nodes = len(ref.children)
    n_supported = np.zeros(n_nodes, dtype=np.int64)
    n_counted = np.zeros(n_nodes, dtype=np.int64)

    def add(result):
        supported, counted = result
        n_supported[:] += np.frombuffer(supported, dtype=np.uint8)
        n_counted[:] += np.frombuffer(counted, dtype=np.uint8)

    def progress_bar():
        return Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            refresh_per_second=1
        )

    description = 'Processing replicate trees'
    if cpus == 1 or len(replicate_trees) == 1:
        _init_worker(ref, hashes)
        try:
            with progress_bar() as p_bar:
                task = p_bar.add_task(description=description, total=len(replicate_trees))
                for rep_path in replicate_trees:
                    add(_score_replicate(rep_path))
                    p_bar.advance(task)
        finally:
            _WORKER.clear()
    else:
        # fork shares the input tree with workers without pickling it; the
        # pool is created before the progress bar starts its refresh thread
        # as forking a multi-threaded process can deadlock the children
        methods = mp.get_all_start_methods()
        ctx = mp.get_context('fork' if 'fork' in methods else None)
        with ctx.Pool(processes=min(cpus, len(replicate_trees)),
                      initializer=_init_worker,
                      initargs=(ref, hashes)) as pool:
            with progress_bar() as p_bar:
                task = p_bar.add_task(description=description, total=len(replicate_trees))
                for result in pool.imap_unordered(_score_replicate, replicate_trees):
                    add(result)
                    p_bar.advance(task)

    # Write the input tree with updated internal labels
    edits = []
    for idx, (start, end) in ref.label_span.items():
        if idx == ref.root:
            continue
        support = None
        if n_counted[idx] > 0:
            support = int(floor(n_supported[idx] * 100.0 / n_counted[idx]))
        edits.append((start, end, _support_label(ref.text[start:end], support)))

    parts = []
    prev = 0
    for start, end, new_label in sorted(edits):
        parts.append(ref.text[prev:start])
        parts.append(new_label)
        prev = end
    parts.append(ref.text[prev:])

    with open(output_tree, 'w') as f:
        f.write(''.join(parts))
    log.info(f'Wrote tree to: {output_tree}')
