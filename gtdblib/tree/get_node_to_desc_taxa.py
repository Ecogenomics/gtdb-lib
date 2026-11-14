from typing import Dict, FrozenSet

import dendropy


def get_tree_node_to_desc_taxa(tree: dendropy.Tree) -> Dict[dendropy.Node, FrozenSet[str]]:
    """Get each node and the taxa that are descendants of this node.

    :param tree: The dendropy tree object to get descendant taxa for.

    :returns: A dictionary of nodes and their descendant taxa.
    """

    # Process nodes in postorder so children are processed before their parent
    out = dict()
    for node in tree.postorder_node_iter():

        # Seed the output dictionary
        if node.is_leaf():
            out[node] = frozenset((node.taxon.label,))

        # Bring up the taxa from the descendant nodes
        else:
            out[node] = frozenset().union(*(out[child] for child in node.child_nodes()))

    assert (out[tree.seed_node] == {x.label for x in tree.taxon_namespace})
    return out
