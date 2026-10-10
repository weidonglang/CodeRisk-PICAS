import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createInterface } from 'node:readline';
import { createHash } from 'node:crypto';

// This dated inventory checks registrations, not relationship labels or detector accuracy.
const root = fileURLToPath(new URL('../../../../', import.meta.url));
const output = process.argv[2];
if (!output || process.argv.length !== 3) {
  throw new Error('Usage: node audit_data.mjs <new-output-directory>');
}
const dir = path.resolve(output);
if (fs.existsSync(dir)) throw new Error('Output must not already exist');
const base = 'coderisk/data/public-datasets/';
const datasets = [
  ['CodeXGLUE / BigCloneBench', 'PUBLISHED_LABEL_DEVELOPMENT', 'codexglue-bcb-20261010/selected_pairs.jsonl'],
  ['PoolC', 'PUBLISHED_LABEL_LICENSE_PENDING', 'poolc-20261010/selected_pairs.jsonl'],
  ['XLCoST', 'UNLABELLED_TITLE_ALIGNED_CANDIDATE', 'xlcost-20261010/selected_pairs.jsonl'],
  ['IR-Plag', 'PUBLISHED_RELATION_PENDING_REVIEW', 'irplag-20261009/published_pairs.jsonl'],
  ['ConPlag v3', 'PUBLISHED_LABEL_EXPLORATORY', 'intake-20261008-v3/conplag-v3/published_pairs.jsonl'],
  ['AD2022', 'UNLABELLED_COURSEWORK_CANDIDATE', 'intake-20261008-v3/ad2022/candidate_pairs.jsonl']
];
const records = [];
for (const [name, scope, file] of datasets) {
  const hash = createHash('sha256'), ids = new Set(), languages = {};
  let count = 0, eligible = 0, synthetic = 0, duplicateIds = 0;
  const stream = fs.createReadStream(path.join(root, base, file));
  stream.on('data', chunk => hash.update(chunk));
  const lines = createInterface({ input: stream, crlfDelay: Infinity });
  for await (const line of lines) {
    if (!line.trim()) continue;
    const row = JSON.parse(line);
    if (!row || typeof row !== 'object' || !row.pair_id) throw new Error('Missing pair identity: ' + file);
    count++;
    if (ids.has(row.pair_id)) duplicateIds++;
    ids.add(row.pair_id);
    eligible += row.eligible_for_core_metrics === true ? 1 : 0;
    synthetic += row.synthetic === true ? 1 : 0;
    if (row.language) languages[row.language] = (languages[row.language] || 0) + 1;
  }
  records.push({ dataset: name, scope, file: base + file, rows: count, uniquePairIdsWithinSource: ids.size,
    duplicatePairIdsWithinSource: duplicateIds, explicitlyEligibleForCoreMetrics: eligible,
    explicitlySynthetic: synthetic, languages, sha256: hash.digest('hex') });
}
const xl = JSON.parse(fs.readFileSync(path.join(root, base, 'xlcost-20261010/audit_summary.json')));
const total = records.reduce((sum, row) => sum + row.rows, 0);
const result = { checkedOn: '2026-10-11', method: 'PARSE_ACTUAL_CURRENT_JSONL_RECORDS_NO_DETECTOR_RUN',
  scope: 'ONE_CURRENT_REGISTRY_PER_SOURCE_NO_REBUILDS_OR_TEMPLATE_FREE_DUPLICATION', records,
  totals: { currentRegisteredPairRows: total, largeSelectedJavaPythonPairs: records[0].rows + records[1].rows,
    crossLanguageCandidates: records[2].rows, olderPublishedRelationRows: records[3].rows + records[4].rows,
    courseworkCandidateRows: records[5].rows,
    explicitlyEligibleForCoreMetrics: records.reduce((sum, row) => sum + row.explicitlyEligibleForCoreMetrics, 0),
    oldDisplayedRegisteredPairRows: 92527, oldDisplayOvercount: 92527 - total },
  xlcost: { tokenizedNotRawSource: true, programRecords: xl.source_records, languages: xl.source_records_by_language },
  exclusionsFromPublicTotal: ['91 synthetic seed pairs', '16 synthetic development probes',
    '1225 service smoke-test enumerated pairs', 'duplicate/rebuilt intake snapshots',
    'upstream full pair references not selected for current pool'],
  limitations: ['Registered rows are not global content-deduplicated pairs.',
    'Published labels are not verified plagiarism/independence facts.',
    'This count check does not verify code semantics, authorization or problem-disjoint evaluation.',
    'No source code executed, detector run, label modified or model call made.'] };
fs.mkdirSync(dir, { recursive: true });
fs.writeFileSync(path.join(dir, 'data_inventory.json'), JSON.stringify(result, null, 2));
console.log(JSON.stringify(result.totals, null, 2));
if (records.some(row => row.duplicatePairIdsWithinSource) || total !== 92513) process.exitCode = 1;
