import os
import tempfile
import unittest

from gtdblib.util.color import TABLEAU_20
from gtdblib.util.shell import color, execute, gtdbshutil


class TestColor(unittest.TestCase):

    def test_rgb_to_hex_zero_padded(self):
        self.assertEqual(color.rgb_to_hex(0, 0, 0), '#000000')
        self.assertEqual(color.rgb_to_hex(1, 2, 255), '#0102FF')

    def test_hex_to_rgb(self):
        self.assertEqual(color.hex_to_rgb('#ff0000'), (255, 0, 0))
        self.assertEqual(color.hex_to_rgb('0102FF'), (1, 2, 255))

    def test_tableau_20(self):
        self.assertEqual(len(TABLEAU_20), 20)
        self.assertEqual(len(set(TABLEAU_20)), 20)


class TestGtdbShutil(unittest.TestCase):

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

    def test_get_num_lines(self):
        self.assertEqual(gtdbshutil.get_num_lines(self._write('empty', '')), 0)
        self.assertEqual(gtdbshutil.get_num_lines(self._write('a', 'x\ny\n')), 2)
        self.assertEqual(gtdbshutil.get_num_lines(self._write('b', 'x\ny')), 2)

    def test_get_num_lines_read_only(self):
        path = self._write('ro', 'x\n')
        os.chmod(path, 0o444)
        self.assertEqual(gtdbshutil.get_num_lines(path), 1)

    def test_symlink_overwrite(self):
        self._write('target1', '1')
        self._write('target2', '2')
        link = os.path.join(self.tmp_dir, 'link')

        self.assertTrue(gtdbshutil.symlink('target1', link))
        with self.assertRaises(FileExistsError):
            gtdbshutil.symlink('target2', link)

        self.assertTrue(gtdbshutil.symlink('target2', link, overwrite=True))
        self.assertEqual(os.readlink(link), 'target2')
        self.assertEqual(sorted(os.listdir(self.tmp_dir)), ['link', 'target1', 'target2'])

    def test_symlink_overwrite_directory(self):
        os.mkdir(os.path.join(self.tmp_dir, 'dir'))
        with self.assertRaises(IsADirectoryError):
            gtdbshutil.symlink('x', os.path.join(self.tmp_dir, 'dir'), overwrite=True)
        self.assertEqual(os.listdir(self.tmp_dir), ['dir'])


class TestExecute(unittest.TestCase):

    def test_run_missing_program(self):
        with self.assertRaises(SystemExit) as cm:
            execute.run(['gtdblib_program_that_does_not_exist'])
        self.assertEqual(cm.exception.code, 1)
