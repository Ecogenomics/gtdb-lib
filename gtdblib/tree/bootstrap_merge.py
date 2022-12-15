import multiprocessing as mp
from math import floor
from pathlib import Path
from typing import Collection

import dendropy
import numpy as np
from rich.progress import track

from gtdblib import log


def bootstrap_merge_replicates(
        input_tree: Path,
        output_tree: Path,
        replicate_trees: Collection[Path],
        cpus: int = 1
):
    """Calculates non-parametric bootstraps for monophyletic groups and
    transposes them to the input tree.

    :param input_tree: The tree to merge the bootstraps to.
    :param output_tree: The path to write the tree to.
    :param replicate_trees: The trees to calculate the bootstraps from.
    :param cpus: The number of processes to use.
    """

    # Validate arguments
    if not isinstance(input_tree, Path):
        raise ValueError(f'Input tree is not a Path object.')
    if not isinstance(output_tree, Path):
        raise ValueError(f'Output tree is not a Path object.')
    if not isinstance(replicate_trees, Collection):
        raise ValueError(f'Replicate trees is not a Collection object.')
    if not all(isinstance(x, Path) for x in replicate_trees):
        raise ValueError(f'Not all replicate trees are Path objects.')
    if cpus is None or not isinstance(cpus, int) or cpus < 1:
        cpus = 1

    # Load the main tree that support values will be added to
    tree = dendropy.Tree.get_from_path(
        str(input_tree),
        schema='newick',
        rooting='force-unrooted',
        preserve_underscores=True
    )

    # Seed the support values
    for node in tree.internal_nodes():
        node.label = 0
        node.nontrivial_splits = 0

    # Store a consistent ordering of the internal nodes
    input_internal_nodes = tuple(tree.internal_nodes(), )

    # Generate the descendant taxa for those nodes
    input_desc_taxa = tuple([frozenset({y.taxon.label for y in x.leaf_nodes()}) for x in input_internal_nodes])

    # Create a queue containing the input descendant taxa and
    queue = list()
    for rep_tree_path in replicate_trees:
        queue.append((rep_tree_path, input_desc_taxa))

    # Calculate the support values single-threaded
    if cpus == 1:
        results = [_calculate_support_worker(x) for x in track(queue, description='Processing...')]

    # Calculate support values with multiple threads
    else:
        with mp.Pool(processes=cpus) as pool:
            results = list(track(
                pool.imap_unordered(_calculate_support_worker, queue),
                description='Processing...',
                total=len(queue)
            ))

    # Append the split information to the nodes
    for result in results:
        for node, (n_support, n_non_trivial_split) in zip(input_internal_nodes, result):
            node.label += n_support
            node.nontrivial_splits += n_non_trivial_split

    # Calculate the %
    for node in tree.internal_nodes():
        if node.nontrivial_splits > 0:
            node.label = str(int(floor(node.label * 100.0 / node.nontrivial_splits)))
        else:
            node.label = 'NA'

    tree.write_to_path(str(output_tree), schema='newick', suppress_rooting=True, unquoted_underscores=True)
    log.info(f'Wrote tree to: {output_tree}')

    return


def _calculate_support_worker(job):
    """A multiprocessing worker to calculate the support for a split."""
    rep_tree_path, taxa_labels = job

    # Create a set that contains the taxa labels in the base tree
    all_ref_taxa_labels = set()
    [all_ref_taxa_labels.update(x) for x in taxa_labels]
    all_ref_taxa_labels = frozenset(all_ref_taxa_labels)

    # Load the tree
    rep_tree = dendropy.Tree.get_from_path(
        str(rep_tree_path),
        schema='newick',
        rooting='force-unrooted',
        preserve_underscores=True
    )
    all_taxa_bitmask = rep_tree.taxon_namespace.all_taxa_bitmask()

    # Calculate the descendant taxa for the reference tree
    rep_tree_list = dendropy.TreeList([rep_tree])
    rep_tree_taxa_set = frozenset({x.taxon.label for x in rep_tree.leaf_node_iter()})

    # Load the common taxa
    common_taxa = rep_tree.taxon_namespace.get_taxa(labels=sorted(rep_tree_taxa_set.intersection(all_ref_taxa_labels)))

    # Determine the width of the largest bit vector
    bit_vector_width = len(np.binary_repr(1 << len(rep_tree.taxon_namespace)))
    bit_array = np.zeros((len(rep_tree.taxon_namespace), bit_vector_width), dtype=np.bool)

    # Get the bitmask for all taxa that are common
    d_taxon_to_idx = dict()
    for i, taxon in enumerate(common_taxa):
        # Generate the bitmask for this taxon
        d_taxon_to_idx[taxon.label] = i
        bitmask = np.binary_repr(
            rep_tree.taxon_namespace.taxon_bitmask(taxon),
            width=bit_vector_width
        )

        # Set the significant bits
        for j, x in enumerate(bitmask):
            if x == '1':
                bit_array[i, j] = True

    # Iterate over the reference tree taxa internal nodes (order is consistent)
    results = list()
    for ref_taxa_labels in taxa_labels:

        # Only calculate the support for splits that are present in the reference tree
        taxa_labels = ref_taxa_labels.intersection(rep_tree_taxa_set)

        # Store the number of supported splits
        if len(taxa_labels) > 1:

            # Get the indices of the bitmask array for these taxa
            taxa_indices = [d_taxon_to_idx[x] for x in taxa_labels]
            split_bit_vec = np.bitwise_or.reduce(bit_array[taxa_indices, :], axis=0)
            split_bit_str = ''.join(['1' if x else '0' for x in split_bit_vec])

            # Calculate the split support
            split = int(split_bit_str, 2)
            normalized_split = dendropy.Bipartition.normalize_bitmask(
                bitmask=split,
                fill_bitmask=all_taxa_bitmask,
                lowest_relevant_bit=1)

            n_support = int(rep_tree_list.frequency_of_bipartition(split_bitmask=normalized_split))
            n_non_trivial_split = 1
        else:
            n_support = 0
            n_non_trivial_split = 0

        # Save the result
        results.append((n_support, n_non_trivial_split))

    # Return the results (in the same order)
    return tuple(results, )