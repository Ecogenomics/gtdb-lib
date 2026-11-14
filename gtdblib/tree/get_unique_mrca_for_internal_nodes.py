from typing import Dict, Tuple

import dendropy


def get_tree_unique_mrca_for_internal_nodes(tree: dendropy.Tree) -> Dict[dendropy.Node, Tuple[str, str]]:
    """Calculate a unique MRCA for each internal node, i.e. using these taxa
    will always yield the same internal node.

    :param tree: The dendropy tree object to calculate unique MRCAs for.

    :returns: A dictionary of nodes and a tuple of each taxon that identifies the node.
    """

    # Determine the first leaf (in preorder) below each node in a single
    # postorder traversal, rather than traversing the subtree of each node
    first_leaf = dict()
    for node in tree.postorder_node_iter():
        if node.is_leaf():
            first_leaf[node] = node.taxon.label
        else:
            first_leaf[node] = first_leaf[node.child_nodes()[0]]

    out = dict()
    for node in tree.internal_nodes():
        child_nodes = node.child_nodes()
        if len(child_nodes) < 2:
            raise ValueError("Node must have at least 2 children")
        left_child = child_nodes[0]
        right_child = child_nodes[1]

        left_taxon = first_leaf[left_child]
        right_taxon = first_leaf[right_child]

        out[node] = (left_taxon, right_taxon)

    return out
