import sys
from collections import defaultdict
from typing import Dict, Iterable, List, Set

from gtdblib import log
from gtdblib.exception import GtdbLibException
from gtdblib.taxon.taxon import Taxon
from gtdblib.util.types import is_float
from gtdblib.util.shell.gtdbshutil import check_file_exists
from gtdblib.util.bio.accession import canonical_gid


def read_taxonomy(taxonomy_file: str, use_canonical_gid: bool = False) -> Dict[str, List[str]]:
    """Read Greengenes-style taxonomy file.

    This method is generic in that it can read any Greengenes-style taxonomy string
    and does not strictly require there to be the seven canonical ranks present.

    Expected format is:
        <accession>\t<taxonomy string>

    where the taxonomy string will typically have the formats:
        d__; c__; o__; f__; g__; s__

    :param taxonomy_file: File indicating Greengenes-style taxonomic assignments.
    :param use_canonical_gid: Flag indicating if accessions should be converted to their canonical form.
    :return: Mapping from accessions to a list of taxa.
    """

    check_file_exists(taxonomy_file)

    row = 0
    try:
        d = {}
        with open(taxonomy_file) as f:
            for row, line in enumerate(f):
                line_split = line.split('\t')
                unique_id = line_split[0]

                if use_canonical_gid:
                    unique_id = canonical_gid(unique_id)

                tax_str = line_split[1].rstrip()
                if tax_str[-1] == ';':
                    # remove trailing semicolons which sometimes
                    # appear in Greengenes-style taxonomy files
                    tax_str = tax_str[0:-1]

                d[unique_id] = [x.strip() for x in tax_str.split(';')]
    except:
        log.error(f'Failed to parse taxonomy file on line {row+1}.')
        raise

    return d


def fill_trailing_ranks(taxa: List[str]) -> List[str]:
    """Fill in missing trailing ranks in a taxonomy string.

    This function assumes it will be provided with a list
    of taxa from the 7 canonical ranks in rank order. Any
    trailing ranks are filled in.

    Example: [d__Bacteria, d__Firmicutes] => [d__Bacteria, d__Firmicutes, c__, o__, f__, g__, s__]

    :param taxa list: List of taxa.

    :return: List of taxa with filled trailing ranks.
    """

    if not taxa:
        return list(Taxonomy.RANK_PREFIXES)

    try:
        last_rank = Taxonomy.RANK_PREFIXES.index(taxa[-1][0:3])
    except:
        log.error('Taxon is missing rank prefix: %s' % ';'.join(taxa))
        sys.exit(1)

    for i in range(last_rank+1, len(Taxonomy.RANK_PREFIXES)):
        taxa.append(Taxonomy.RANK_PREFIXES[i])

    return taxa


def read_taxonomy_from_tree(tree: str, warnings: bool = True) -> Dict[str, List[str]]:
    """Obtain the taxonomy for each extant taxa as specified by internal tree labels.

    This method is generic in that it can read any Greengenes-style taxonomy string
    and does not strictly require extran taxa to be classified to theseven canonical ranks.

    :param tree: Filename of Newick tree or Dendropy tree object.
    :param warnings: Flag indicating if issues reading tree should be logged as warnings.

    :return: Mapping from extent taxon labels to a list of taxa.
    """

    if isinstance(tree, str):
        import dendropy
        tree = dendropy.Tree.get_from_path(tree,
                                           schema='newick',
                                           rooting="force-rooted",
                                           preserve_underscores=True)

    taxonomy = {}
    for leaf in tree.leaf_node_iter():
        taxa = []

        node = leaf.parent_node
        while node:
            if node.label:
                taxa_str = node.label
                if ':' in taxa_str:
                    taxa_str = taxa_str.split(':')[1]

                if not is_float(taxa_str):
                    if taxa_str[-1] == ';':
                        taxa_str = taxa_str[:-1]

                    # check for concatenated ranks of the form: p__Crenarchaeota__c__Thermoprotei
                    for prefix in Taxonomy.RANK_PREFIXES:
                        split_str = '__' + prefix
                        if split_str in taxa_str:
                            taxa_str = taxa_str.replace(
                                split_str, ';' + prefix)

                    # appears to be an internal label and not simply a support value
                    taxa = [x.strip() for x in taxa_str.split(';')] + taxa
            node = node.parent_node

        if warnings and len(taxa) > len(Taxonomy.RANK_LABELS):
            log.warning('Invalid taxonomy string read from tree for taxon {}: {}'.format(
                leaf.taxon.label,
                ';'.join(taxa)))

        # check if genus name should be appended to species label as some trees
        # indicate species only by their specific epithet
        if len(taxa) == len(Taxonomy.RANK_LABELS):
            genus = taxa[5][3:]
            species = taxa[6][3:]
            if genus not in species and len(species.split()) == 1:
                taxa[6] = 's__' + genus + ' ' + species

        taxa = fill_trailing_ranks(taxa)
        taxonomy[leaf.taxon.label] = taxa

    return taxonomy


def write_taxonomy(taxonomy: Dict[str, List[str]], output_file: str):
    """Write Greengenes-style taxonomy file.

    :param taxonomy: Mapping from accessions to a list of taxa.
    :param output_file: File to write taxonomy to.
    """

    with open(output_file, 'w') as fout:
        for unique_id, taxa in taxonomy.items():
            fout.write(f'{unique_id}\t{";".join(taxa)}\n')


def fill_missing_ranks(taxa: List[str], warning: bool = True) -> List[str]:
    """Fill in missing internal and trailing ranks.

    Taxa are assumed to be in rank order, but some ranks may be missing or
    repeated (e.g. [d__Bacteria, p__Firmicutes, p__Firmicutes_A, f__Bacillaceae]).

    Example: [d__Bacteria, c__Bacilli, g__Bacillus] => [d__Bacteria, p__, c__Bacilli, o__, f__, g__Bacillus, s__]

    :param taxa: List of taxa.
    :param warning: Flag indicating if a warning should be logged for taxa that are
        not in canonical rank order.

    :return: List of taxa with all missing ranks filled in, or the original taxa
        if they are not in canonical rank order.
    """

    new_taxa = []
    prev_rank_index = -1
    for taxon in taxa:
        rank_index = Taxonomy.RANK_INDEX.get(taxon[0:3])
        if rank_index is None:
            raise GtdbLibException(f'Taxon is missing rank prefix: {taxon}')

        if rank_index < prev_rank_index:
            if warning:
                log.warning(f'Taxa have non-canonical rank ordering: {";".join(taxa)}')
            return list(taxa)

        # add any missing ranks before this taxon
        new_taxa.extend(Taxonomy.RANK_PREFIXES[prev_rank_index + 1:rank_index])
        new_taxa.append(taxon)
        prev_rank_index = rank_index

    return fill_trailing_ranks(new_taxa)


def check_full_taxonomy(tax_str: str) -> bool:
    """Check if a taxonomy string contains exactly the 7 canonical ranks in order.

    Problems with the taxonomy string are logged as errors.

    :param tax_str: Taxonomy string (e.g. d__Bacteria;p__;...;s__).

    :return: True if the taxonomy string is complete, else False.
    """

    taxa = [x.strip() for x in tax_str.split(';')]
    if len(taxa) < len(Taxonomy.RANK_PREFIXES):
        log.error(f'Taxonomy string contains too few ranks: {taxa}')
        return False
    elif len(taxa) > len(Taxonomy.RANK_PREFIXES):
        log.error(f'Taxonomy string contains too many ranks: {taxa}')
        return False

    for prefix, taxon in zip(Taxonomy.RANK_PREFIXES, taxa):
        if taxon[0:3] != prefix:
            log.error(f'Taxon is not prefixed with the expected rank, {prefix}: {taxa}')
            return False

    return True


def extant_taxa_for_rank(rank_label: str, taxonomy: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """Get the extant taxa (e.g. genomes) in each named group at a rank.

    :param rank_label: Rank of interest (e.g. 'class').
    :param taxonomy: Mapping from accessions to a list of taxa for the 7 canonical ranks.

    :return: Mapping from each named taxon at the rank to the accessions it contains.
    """

    if rank_label not in Taxonomy.RANK_LABELS:
        raise GtdbLibException(f'Unknown rank: {rank_label}')

    rank_index = Taxonomy.RANK_LABELS.index(rank_label)
    rank_prefix = Taxonomy.RANK_PREFIXES[rank_index]

    d = defaultdict(set)
    for unique_id, taxa in taxonomy.items():
        if taxa[rank_index] != rank_prefix:
            d[taxa[rank_index]].add(unique_id)

    return d


def extant_taxa(taxonomy: Dict[str, List[str]]) -> Dict[str, Set[str]]:
    """Get the extant taxa (e.g. genomes) in each named group at all ranks.

    :param taxonomy: Mapping from accessions to a list of taxa for the 7 canonical ranks.

    :return: Mapping from each named taxon to the accessions it contains.
    """

    d = {}
    for rank_label in Taxonomy.RANK_LABELS:
        d.update(extant_taxa_for_rank(rank_label, taxonomy))

    return d


def sort_taxa(taxa: Iterable[str], reverse: bool = False) -> List[str]:
    """Sort taxa by rank (domain to species) and then alphabetically.

    :param taxa: Taxa to sort, each with a rank prefix (e.g. p__Firmicutes).
    :param reverse: Flag indicating if the order should be reversed.

    :return: Sorted list of taxa. Taxa without a canonical rank prefix are omitted.
    """

    taxa = list(taxa)
    ordered_taxa = []
    for rank_prefix in Taxonomy.RANK_PREFIXES:
        ordered_taxa.extend(sorted(t for t in taxa if t.startswith(rank_prefix)))

    if reverse:
        ordered_taxa.reverse()

    return ordered_taxa


class Taxonomy:
    __slots__ = ('d', 'p', 'c', 'o', 'f', 'g', 's')

    RANK_PREFIXES = ('d__', 'p__', 'c__', 'o__', 'f__', 'g__', 's__')
    RANK_LABELS = ('domain', 'phylum', 'class', 'order',
                   'family', 'genus', 'species')
    RANK_INDEX = {'d__': 0, 'p__': 1, 'c__': 2,
                  'o__': 3, 'f__': 4, 'g__': 5, 's__': 6}

    DOMAIN_INDEX = 0
    PHYLUM_INDEX = 1
    CLASS_INDEX = 2
    ORDER_INDEX = 3
    FAMILY_INDEX = 4
    GENUS_INDEX = 5
    SPECIES_INDEX = 6

    def __init__(self, d: Taxon, p: Taxon, c: Taxon, o: Taxon, f: Taxon, g: Taxon, s: Taxon):
        self.d = d
        self.p = p
        self.c = c
        self.o = o
        self.f = f
        self.g = g
        self.s = s
