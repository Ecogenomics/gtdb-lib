import gzip
import os
import tempfile
import unittest

from gtdblib.util.bio import seq_io


class TestSeqIO(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = self._tmp.name

    def tearDown(self):
        self._tmp.cleanup()

    def _write(self, name, content):
        path = os.path.join(self.tmp_dir, name)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def test_read_fasta_seq_empty_file(self):
        path = self._write('empty.fna', '')
        self.assertEqual(list(seq_io.read_fasta_seq(path)), [])
        self.assertEqual(list(seq_io.read_seq(path)), [])

    def test_read_fasta_seq_blank_lines_only(self):
        path = self._write('blank.fna', '\n\n')
        self.assertEqual(list(seq_io.read_fasta_seq(path)), [])

    def test_read_fastq(self):
        path = self._write('reads.fq', '@r1 desc\nACGT\n+\nIIII\n@r2\nGG\n+\nII\n')
        self.assertEqual(seq_io.read_fastq(path), {'r1': 'ACGT', 'r2': 'GG'})

    def test_read_fastq_extension(self):
        content = '@r1\nACGT\n+\nIIII\n'
        for ext in ('.fq', '.fastq'):
            path = self._write('reads' + ext, content)
            self.assertEqual(seq_io.read(path), {'r1': 'ACGT'})
            self.assertEqual(list(seq_io.read_seq(path)), [('r1', 'ACGT')])

    def test_extract_seqs_header_without_description(self):
        path = self._write('seqs.fna', '>s1\nACGT\n>s2 desc\nGG\n>s3\nTT\n')
        self.assertEqual(seq_io.extract_seqs(path, {'s1', 's2'}), {'s1': 'ACGT', 's2': 'GG'})

    def test_write_fasta_gz(self):
        path = os.path.join(self.tmp_dir, 'out.fna.gz')
        seq_io.write_fasta({'a': 'ACGT', 'b': 'GG'}, path, wrap=2)
        with gzip.open(path, 'rt') as f:
            self.assertEqual(f.read(), '>a\nAC\nGT\n>b\nGG\n')
        self.assertEqual(seq_io.read_fasta(path), {'a': 'ACGT', 'b': 'GG'})

    def test_is_protein_nucleotide_file(self):
        path = self._write('genes.fna', '>s1\nACGTACGTAC\n')
        self.assertTrue(seq_io.is_nucleotide(path))
        self.assertFalse(seq_io.is_protein(path))

    def test_is_protein_protein_file(self):
        path = self._write('genes.faa', '>s1\nMKLVWRQEDHIPSTAG\n')
        self.assertFalse(seq_io.is_nucleotide(path))
        self.assertTrue(seq_io.is_protein(path))
