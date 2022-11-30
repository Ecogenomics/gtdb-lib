from collections import defaultdict
from pathlib import Path
from typing import Collection

import dendropy
from rich.progress import track

from gtdblib import log
from gtdblib.exception import GtdbLibExit
from gtdblib.tree.get_node_to_desc_taxa import get_tree_node_to_desc_taxa
from gtdblib.util.bio.newick import parse_label, create_label


def _load_newick(path: Path):
    return dendropy.Tree.get_from_path(
        str(path),
        schema='newick',
        rooting='force-unrooted',
        preserve_underscores=True
    )


def bootstrap_merge_replicates(input_tree: Path, output_tree: Path, replicate_trees: Collection[Path]):
    """Calculates non-parametric bootstraps for monophyletic groups and
    transposes them to the input tree.

    :param input_tree: The tree to merge the bootstraps to.
    :param output_tree: The path to write the tree to.
    :param replicate_trees: The trees to calculate the bootstraps from.
    """

    n_replicates = len(replicate_trees)

    log.info(f'Loading input tree: {input_tree}')
    orig_tree = _load_newick(input_tree)
    orig_taxa = {x.label for x in orig_tree.taxon_namespace}

    # 1. Get the unique monophyletic groups in the original tree
    d_orig_node_to_desc_taxa = get_tree_node_to_desc_taxa(orig_tree)

    # 2. Load the replicate trees and calculate the unique monophyletic groups
    log.info('Loading replicate trees')
    d_rep_desc_taxa_to_count = defaultdict(lambda: 0)
    for replicate_tree in track(replicate_trees, description="Processing..."):
        rep_tree = _load_newick(replicate_tree)
        rep_taxa = {x.label for x in rep_tree.taxon_namespace}
        if orig_taxa != rep_taxa:
            raise GtdbLibExit(f'Input tree and replicate tree taxa do not match: {input_tree} {replicate_tree}')

        d_rep_node_to_desc_taxa = get_tree_node_to_desc_taxa(rep_tree)
        for rep_desc_taxa_set in d_rep_node_to_desc_taxa.values():
            d_rep_desc_taxa_to_count[rep_desc_taxa_set] += 1

    # 3. Annotate each of the labels with the bootstrap value
    for node, desc_taxa in d_orig_node_to_desc_taxa.items():
        if node.is_leaf():
            continue

        n_observed = d_rep_desc_taxa_to_count[desc_taxa]
        bootstrap = round(100 * n_observed / n_replicates, 2)

        if node.label:
            support, taxon, aux_info = parse_label(node.label)
            node.label = create_label(bootstrap, taxon, aux_info)
        else:
            node.label = str(bootstrap)

    # 4. Write the tree to disk
    orig_tree.write_to_path(str(output_tree),
                            schema='newick',
                            suppress_rooting=True,
                            unquoted_underscores=True)
    log.info(f'Wrote tree to: {output_tree}')

    return
