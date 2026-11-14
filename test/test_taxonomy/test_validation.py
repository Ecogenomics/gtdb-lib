import contextlib
import io
import unittest

from gtdblib.taxonomy.validation import duplicate_names, validate_species_name, validate_taxonomy


def _validate(taxonomy):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        result = validate_taxonomy(taxonomy,
                                   check_prefixes=True,
                                   check_ranks=True,
                                   check_hierarchy=True,
                                   check_species=True,
                                   check_group_names=True,
                                   check_duplicate_names=True,
                                   check_capitalization=True,
                                   report_errors=True)
    return result, out.getvalue()


class TestValidation(unittest.TestCase):

    def test_validate_taxonomy_valid(self):
        taxonomy = {
            'G1': ['d__B', 'p__P', 'c__C', 'o__O', 'f__F', 'g__Gen', 's__Gen sp1'],
            'G2': ['d__B', 'p__P', 'c__C', 'o__O', 'f__F', 'g__Gen', 's__Gen sp1'],
            'G3': ['d__B', 'p__P', 'c__C', 'o__O', 'f__F_A', 'g__Other', 's__'],
        }
        result, out = _validate(taxonomy)
        self.assertEqual(len(result), 6)
        self.assertEqual(result, ({}, {}, {}, {}, {}, set()))
        self.assertEqual(out, '')

    def test_validate_taxonomy_invalid(self):
        taxonomy = {
            'G1': ['d__B', 'p__P1', 'c__C', 'o__O', 'f__F', 'g__Gen', 's__Gen sp1'],
            'G2': ['d__B', 'p__P2', 'c__C', 'o__O', 'f__F', 'g__Gen', 's__Gen sp1'],
            'G3': ['d__B', 'p__P1', 'c__C', 'o__O', 'f__F'],
            'G4': ['d__B', 'p__P1', 'x__C', 'o__O', 'f__F', 'g__Gen', 's__Gen sp1'],
            'G5': ['d__B', 'p__P1', 'c__C', 'o__O', 'f__F', 'g__Gen', 's__Gen bacterium'],
            'G6': ['d__B', 'p__P1', 'c__C', 'o__O', 'f__F', 'g__bad$', 's__'],
        }
        (invalid_ranks, invalid_prefixes, invalid_species_name, invalid_hierarchies,
         invalid_group_name, invalid_capitalization), out = _validate(taxonomy)

        self.assertEqual(invalid_ranks, {'G3': 'd__B;p__P1;c__C;o__O;f__F'})
        self.assertEqual(invalid_prefixes, {'G4': ['x__C', 'd__B;p__P1;x__C;o__O;f__F;g__Gen;s__Gen sp1']})
        self.assertEqual(invalid_species_name, {'G5': ['s__Gen bacterium', "name contains the word 'bacterium'"]})
        self.assertEqual(invalid_hierarchies, {'c__C': {'p__P1', 'p__P2'}, 'o__O': {'c__C', 'x__C'}})
        self.assertEqual(invalid_group_name, {'G6': ['g__bad$', 'Taxon contains invalid characters']})
        self.assertEqual(invalid_capitalization, {'g__bad$'})
        self.assertIn('Taxonomy contains an invalid number of ranks:', out)
        self.assertIn('c__C\tp__P1, p__P2', out)

    def test_duplicate_names(self):
        taxonomy = {
            'G1': ['d__B', 'p__P1', 'c__C', 's__X y'],
            'G2': ['d__B', 'p__P2', 'c__C', 's__X y'],
            'G3': ['d__B', 'p__P2', 'c__C', 's__X y'],
        }
        self.assertEqual(duplicate_names(taxonomy), {
            'c__C': {'d__B;p__P1;c__C', 'd__B;p__P2;c__C'},
            's__X y': {'d__B;p__P1;c__C;s__X y', 'd__B;p__P2;c__C;s__X y'},
        })
        self.assertEqual(list(duplicate_names(taxonomy, check_species=False)), ['c__C'])

    def test_validate_species_name(self):
        self.assertEqual(validate_species_name('s__'), (True, None))
        self.assertEqual(validate_species_name('s__Escherichia coli'), (True, None))
        self.assertEqual(validate_species_name('Escherichia coli'),
                         (False, 'name is missing the species prefix'))
        self.assertEqual(validate_species_name('s__coli'),
                         (False, 'name appears to be missing the generic name'))
        self.assertEqual(validate_species_name('s__Escherichia Symbiont-like'),
                         (False, "name contains '-like'"))
        self.assertEqual(validate_species_name('s__escherichia coli'),
                         (False, 'first letter of name is lowercase'))


if __name__ == '__main__':
    unittest.main()
