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


GIDS = {'G000830295', 'G001595785', 'G001871415', 'G002498125', 'G002503705', 'G002505525', 'G002505945', 'G002506365',
        'G002685855', 'G002686295', 'G002686315', 'G002686855', 'G002687275', 'G002687775', 'G002687795', 'G002688265',
        'G002688315', 'G002688775', 'G002688925', 'G002762705', 'G002762785', 'G002762795', 'G002762845', 'G002762865',
        'G002762915', 'G002762985', 'G002763025', 'G002763335', 'G002779235', 'G002792115', 'G002867475', 'G003560545',
        'G003561825', 'G003562145', 'G003564925', 'G003599055', 'G003599145', 'G003648985', 'G003650545', 'G003650585',
        'G003694385', 'G003694525', 'G003694805', 'G003695045', 'G003695265', 'G003695435', 'G005222965', 'G007116295',
        'G007116645', 'G007117065', 'G007117145', 'G007117405', 'G007117735', 'G007117755', 'G007128245', 'G007131205',
        'G011045925', 'G011329125', 'G011331795', 'G011368255', 'G011372335', 'G013152815', 'G013202845', 'G013202955',
        'G013203345', 'G013204355', 'G013215525', 'G013329045', 'G013329175', 'G013330595', 'G013330825', 'G013331125',
        'G013331515', 'G013331555', 'G013331575', 'G013331615', 'G013331635', 'G013331695', 'G013331965', 'G013335235',
        'G014384375', 'G014728875', 'G014729015', 'G014729145', 'G014729195', 'G014729345', 'G014729495', 'G014729505',
        'G014729555', 'G014729675', 'G014729915', 'G014729995', 'G014874255', 'G015519985', 'G015520525', 'G015520785',
        'G015522765', 'G016177315', 'G016177345', 'G016177615', 'G016179955', 'G016179995', 'G016180035', 'G016180065',
        'G016180085', 'G016180105', 'G016180135', 'G016180145', 'G016180165', 'G016180195', 'G016180235', 'G016180275',
        'G016180285', 'G016181265', 'G016181305', 'G016181325', 'G016181345', 'G016184145', 'G016184345', 'G016185625',
        'G016185685', 'G016185705', 'G016185725', 'G016185755', 'G016185805', 'G016185815', 'G016185845', 'G016185865',
        'G016185875', 'G016185915', 'G016185945', 'G016185955', 'G016187465', 'G016187495', 'G016187565', 'G016188105',
        'G016188115', 'G016188145', 'G016188155', 'G016188175', 'G016188205', 'G016188215', 'G016188245', 'G016188265',
        'G016192905', 'G016192915', 'G016192945', 'G016192955', 'G016192985', 'G016192995', 'G016198725', 'G016203205',
        'G016203215', 'G016203225', 'G016203265', 'G016203305', 'G016203335', 'G016203345', 'G016203375', 'G016203395',
        'G016203425', 'G016203445', 'G016205905', 'G016208715', 'G016211165', 'G016211185', 'G016211195', 'G016211215',
        'G016211245', 'G016213425', 'G016213985', 'G016214025', 'G016214075', 'G016215305', 'G016215315', 'G016219765',
        'G016219795', 'G016219835', 'G016219865', 'G016784105', 'G016784125', 'G016784165', 'G016784195', 'G016926055',
        'G016926395', 'G016927245', 'G016928115', 'G016928155', 'G016928835', 'G016929255', 'G016929855', 'G016929895',
        'G016930415', 'G016932315', 'G016932755', 'G016933095', 'G016934775', 'G016935095', 'G016935125', 'G016935155',
        'G016935175', 'G016935265', 'G016935985', 'G016938695', 'G017608295', 'G017608625', 'G017609245', 'G017609385',
        'G017609645', 'G017610005', 'G017610275', 'G017610505', 'G018221085', 'G018221105', 'G018221125', 'G018221135',
        'G018221165', 'G018221175', 'G018221205', 'G018221245', 'G018263355', 'G018302085', 'G018302185', 'G018302335',
        'G018302605', 'G018302815', 'G018303045', 'G018303075', 'G018303105', 'G018303115', 'G018303125', 'G018303185',
        'G018303205', 'G018303225', 'G018303245', 'G018303265', 'G018303285', 'G018303315', 'G018303325', 'G018303405',
        'G018303425', 'G018303445', 'G018303505', 'G018303575', 'G018303625', 'G018303645', 'G018303655', 'G018303685',
        'G018303725', 'G018399355', 'G018646625', 'G018653365', 'G018655525', 'G018657065', 'G018657385', 'G018657475',
        'G018657845', 'G018661705', 'G018664115', 'G018668595', 'G018670085', 'G018670095', 'G018671515', 'G018675335',
        'G018675975', 'G018676855', 'G018696395', 'G018696595', 'G018697095', 'G018812355', 'G018812465', 'G018812505',
        'G018812765', 'G018813685', 'G018813725', 'G018815145', 'G018816705', 'G018817005', 'G018819065', 'G018819305',
        'G018819345', 'G018824365', 'G018825425', 'G018830225', 'G018901315', 'G902385765', 'G902529885', 'G903842985',
        'G903891505', 'G903904885', 'G903907555', 'G903915225'}


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
    i = 0
    for replicate_tree in track(replicate_trees, description="Processing..."):
        print(i)
        i += 1
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
