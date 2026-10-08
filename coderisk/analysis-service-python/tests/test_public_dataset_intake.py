"""Data-contract regression tests; all sample archives are artificial test fixtures."""
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'experiment'))
from acquire_public_datasets import csv_rows, import_ad2022, import_conplag, read_split, verify_archive, verify_intake


def csv_text(fields, rows):
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def conplag_fixture(path, *, unsafe=False, unknown_split=False):
    labels = [
        {'sub1': '00000001', 'sub2': '00000002', 'problem': '1', 'verdict': '1'},
        {'sub1': '00000001', 'sub2': '00000003', 'problem': '1', 'verdict': '0'},
        {'sub1': '00000004', 'sub2': '00000005', 'problem': '2', 'verdict': '0'},
        {'sub1': '00000004', 'sub2': '00000006', 'problem': '2', 'verdict': '1'},
    ]
    if unsafe:
        labels[0]['sub1'] = '../escape'
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr('README.md', 'Artificial contract fixture')
        archive.writestr('versions/labels.csv', csv_text(['sub1', 'sub2', 'problem', 'verdict'], labels))
        archive.writestr('versions/train_pairs.csv', '00000001_00000002\n00000004_00000005\n')
        test = '00000001_00000003\n00000004_00000006\n'
        archive.writestr('versions/test_pairs.csv', test + ('00000007_00000008\n' if unknown_split else ''))
        for index, row in enumerate(labels):
            pair = '_'.join(sorted((row['sub1'], row['sub2'])))
            for version in ('version_1', 'version_2'):
                for sid in (row['sub1'], row['sub2']):
                    archive.writestr(f'versions/{version}/{pair}/{sid}.java', f'class S{sid} {{ int v = {index}; }}\r\n')


class PublicIntakeTests(unittest.TestCase):
    def test_headerless_split_keeps_first_pair_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.zip'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('ok', '00000001_00000002\n00000003_00000004\n')
                archive.writestr('duplicate', '00000001_00000002\n00000001_00000002\n')
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(len(read_split(archive, 'ok')), 2)
                self.assertEqual(read_split(archive, 'ok')[0], '00000001_00000002')
                with self.assertRaises(ValueError):
                    read_split(archive, 'duplicate')

    def test_variant_bytes_are_preserved_and_published_labels_are_not_promoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, output = Path(tmp) / 'data.zip', Path(tmp) / 'intake'
            conplag_fixture(path)
            summary, proposal = import_conplag(path, output, 42)
            self.assertEqual(summary['published_pairs'], 4)
            self.assertEqual(summary['submission_ids_with_multiple_raw_byte_versions'], 2)
            self.assertEqual(summary['upstream_split_overlap_counts']['submission_ids'], 2)
            pairs = [json.loads(row) for row in (output / 'published_pairs.jsonl').read_text().splitlines()]
            self.assertTrue(all(row['experiment_label'] == 'UNCERTAIN' and not row['eligible_for_core_metrics'] for row in pairs))
            self.assertEqual({row['published_verdict'] for row in pairs}, {0, 1})
            split = {row['pair_id']: row['proposed_split'] for row in proposal['rows']}
            self.assertEqual(split[pairs[0]['pair_id']], split[pairs[1]['pair_id']])
            self.assertNotEqual(split[pairs[0]['pair_id']], split[pairs[2]['pair_id']])
            self.assertTrue(all(not row['split_preregistered'] for row in proposal['rows']))
            with zipfile.ZipFile(path) as archive:
                for row in pairs:
                    for files in row['files'].values():
                        for record in files:
                            self.assertEqual((output / record['code_path']).read_bytes(), archive.read(record['code_path']))

    def test_unexpected_split_pair_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.zip'
            conplag_fixture(path, unknown_split=True)
            with self.assertRaisesRegex(ValueError, 'unknown pairs'):
                import_conplag(path, Path(tmp) / 'intake', 42)

    def test_untrusted_submission_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.zip'
            conplag_fixture(path, unsafe=True)
            with self.assertRaisesRegex(ValueError, 'Invalid ConPlag'):
                import_conplag(path, Path(tmp) / 'intake', 42)
            self.assertFalse((Path(tmp) / 'escape').exists())

    def test_csv_large_fields_and_embedded_line_endings_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.zip'
            code = 'a\r\nb\n' + 'x' * 150000
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('test.csv', csv_text(['solution'], [{'solution': code}]))
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(csv_rows(archive, 'test.csv')[0]['solution'], code)

    def test_ad_repeated_rows_preserved_without_inferred_independent_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            path, output = Path(tmp) / 'data.zip', Path(tmp) / 'intake'
            code = 'int f() {\r\n return 1;\r\n}'
            with zipfile.ZipFile(path, 'w') as archive:
                archive.writestr('AD2022dataset/README.md', 'Artificial fixture')
                archive.writestr('AD2022dataset/Licence.txt', 'Artificial fixture')
                for term in ('19_20', '20_21', '21_22'):
                    prefix = 'AD2022dataset/' + term
                    qid = term + '-1-1-java'
                    archive.writestr(prefix + '_task_descriptions.csv', csv_text(['id'], [{'id': qid}]))
                    rows = [{'question_id': qid, 'student_id': sid, 'solution': code} for sid in ('ABCD1234', 'ABCD1234', 'EFGH5678')]
                    archive.writestr(prefix + '_solutions.csv', csv_text(['question_id', 'student_id', 'solution'], rows))
                    archive.writestr(prefix + '_tests.csv', csv_text(['question_id'], [{'question_id': qid}]))
            summary = import_ad2022(path, output)
            self.assertEqual(summary['solutions'], 9)
            self.assertEqual(summary['candidate_pairs'], 3)
            self.assertEqual(summary['published_pair_labels'], 0)
            self.assertEqual(summary['pseudonyms_observed_in_multiple_terms'], 2)
            self.assertEqual((output / 'sources/AD2022-19_20-0001.java').read_bytes(), code.encode())
            candidates = [json.loads(row) for row in (output / 'candidate_pairs.jsonl').read_text().splitlines()]
            self.assertTrue(all(row['experiment_label'] == 'UNCERTAIN' and not row['eligible_for_core_metrics'] for row in candidates))

    def test_bad_checksum_rejected_before_intake(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.zip'
            path.write_bytes(b'changed')
            source = {'id': 'test', 'size_bytes': 7, 'sha256': hashlib.sha256(b'original').hexdigest(), 'md5': '0' * 32}
            with self.assertRaisesRegex(ValueError, 'Checksum mismatch'):
                verify_archive(path, source)

    def test_intake_inventory_rejects_changed_code_and_outside_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            (output / 'code.java').write_bytes(b'class A {}')
            inventory = [{'path': 'code.java', 'size_bytes': 10, 'sha256': hashlib.sha256(b'class A {}').hexdigest()}]
            (output / 'file_inventory.json').write_text(json.dumps(inventory))
            (output / 'intake_summary.json').write_text(json.dumps({'status': 'INTAKE_COMPLETE_NO_DETECTOR_SCORES', 'inventory_files': 1}))
            self.assertEqual(verify_intake(output)['verified_files'], 1)
            (output / 'code.java').write_bytes(b'class B {}')
            with self.assertRaisesRegex(ValueError, 'content changed'):
                verify_intake(output)
            inventory[0]['path'] = '../outside.java'
            (output / 'file_inventory.json').write_text(json.dumps(inventory))
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                verify_intake(output)


if __name__ == '__main__':
    unittest.main()
