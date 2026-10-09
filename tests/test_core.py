"""Hand-built correctness oracles. Never call the admitted evaluation."""
import copy
import math
import unittest
from lexical_retrieval_bench.core import answer, metrics, rank, tokenize, validate_request
from lexical_retrieval_bench.demo import REQUEST


class RankingTests(unittest.TestCase):
    def setUp(self):
        self.docs = copy.deepcopy(REQUEST['documents'])

    def test_hand_scores_and_repeat_oov(self):
        expected = {'overlap': 1, 'tfidf': 1,
                    'bm25': math.log(3) * 4.4 / 4.1}
        for ranker, value in expected.items():
            with self.subTest(ranker=ranker):
                rows = rank(self.docs, 'amber amber absent', ranker)
                self.assertEqual([r['document_id'] for r in rows], ['a', 'b', 'c'])
                self.assertAlmostEqual(rows[0]['score'], value, places=14)
                self.assertEqual(rows[1]['score'], 0)
                self.assertEqual(rows[2]['score'], 0)
                self.assertEqual(rows, rank(list(reversed(self.docs)), 'amber', ranker))
                for row in rows:
                    self.assertEqual(row['score'], sum(t['contribution'] for t in row['matched_terms']))

    def test_tfidf_independent_oracle(self):
        docs = [{'id': 'a', 'text': 'amber blue'}, {'id': 'b', 'text': 'amber'}]
        i = 1 + math.log(1.5)
        self.assertAlmostEqual(rank(docs, 'blue', 'tfidf')[0]['score'], i / math.sqrt(1 + i * i), places=14)

    def test_ubiquitous_bm25_and_ties(self):
        docs = [{'id': 'z', 'text': 'amber'}, {'id': 'a', 'text': 'amber amber'}]
        rows = rank(docs, 'amber', 'bm25')
        self.assertEqual([r['document_id'] for r in rows], ['a', 'z'])
        self.assertEqual([r['score'] for r in rows], [0, 0])
        self.assertEqual(rows[0]['matched_terms'], [{'term': 'amber', 'contribution': 0.0}])

    def test_empty_absent_and_cutoff(self):
        for ranker in ('overlap', 'tfidf', 'bm25'):
            for query in ('', 'unseen'):
                rows = rank(self.docs, query, ranker, 2)
                self.assertEqual([r['document_id'] for r in rows], ['a', 'b'])
                self.assertEqual([r['score'] for r in rows], [0, 0])
            docs = [{'id': 'z', 'text': ''}, {'id': 'a', 'text': ''}]
            self.assertEqual([r['document_id'] for r in rank(docs, '', ranker, 10)], ['a', 'z'])

    def test_ascii_token_contract(self):
        self.assertEqual(tokenize('ÁMBER—Blue_42\nA\tB １２ e\u0301'), ['mber', 'blue', '42', 'a', 'b', 'e'])
        with self.assertRaises(ValueError):
            tokenize('\ud800')

    def test_direct_api_invalid(self):
        cases = [(self.docs, 'a', 'unknown', 1), (self.docs, 'a', 'overlap', True),
                 (self.docs, 'a', 'overlap', 0), (self.docs, 'a', 'overlap', 11),
                 ([], 'a', 'overlap', 1), (self.docs * 2, 'a', 'overlap', 1),
                 ([{'id': '../x', 'text': ''}], '', 'overlap', 1),
                 (self.docs, 'a ' * 33, 'overlap', 1)]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(ValueError):
                rank(*args)

    def test_schema_and_display_k_independent_metrics(self):
        request = copy.deepcopy(REQUEST)
        request['k'] = 1
        result = answer(request)
        self.assertEqual(len(result['results'][0]['ranking']), 1)
        self.assertEqual(result['results'][0]['metrics'], {'recall_at_5': 1, 'mrr_at_10': 1, 'ndcg_at_10': 1})
        for change in ('duplicate_query', 'duplicate_qrel', 'unknown_doc', 'duplicate_grade', 'bool_grade', 'extra'):
            bad = copy.deepcopy(REQUEST)
            if change == 'duplicate_query':
                bad['queries'] *= 2
            elif change == 'duplicate_qrel':
                bad['qrels'] *= 2
            elif change == 'unknown_doc':
                bad['qrels'][0]['grades'][0]['document_id'] = 'missing'
            elif change == 'duplicate_grade':
                bad['qrels'][0]['grades'] *= 2
            elif change == 'bool_grade':
                bad['qrels'][0]['grades'][0]['grade'] = True
            else:
                bad['documents'][0]['extra'] = 1
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_request(bad)


class MetricTests(unittest.TestCase):
    def test_independent_graded_and_partial_oracles(self):
        grades = {'a': 2, 'b': 1, 'c': 1}
        ids = ['a', 'b', 'c', 'x']
        ideal = 3 + 1 / math.log2(3) + 0.5
        got = metrics(['x', 'b', 'a', 'c'], grades, ids)
        self.assertEqual(got['recall_at_5'], 1)
        self.assertEqual(got['mrr_at_10'], 0.5)
        self.assertAlmostEqual(got['ndcg_at_10'], (1 / math.log2(3) + 1.5 + 1 / math.log2(5)) / ideal, places=14)
        got = metrics(['x', 'b'], grades, ids)
        self.assertEqual(got['recall_at_5'], 1 / 3)
        self.assertEqual(got['mrr_at_10'], 0.5)
        self.assertAlmostEqual(got['ndcg_at_10'], (1 / math.log2(3)) / ideal, places=14)

    def test_cutoffs(self):
        ids = ['d' + str(i) for i in range(11)]
        for position in (5, 6, 10, 11):
            got = metrics(ids, {ids[position - 1]: 1}, ids)
            self.assertEqual(got['recall_at_5'], int(position <= 5))
            self.assertEqual(got['mrr_at_10'], 1 / position if position <= 10 else 0)
            self.assertAlmostEqual(got['ndcg_at_10'], 1 / math.log2(position + 1) if position <= 10 else 0)

    def test_zero_and_invalid(self):
        for grades in ({}, {'a': 0}):
            self.assertEqual(metrics(['a'], grades, ['a']), {'recall_at_5': 0, 'mrr_at_10': 0, 'ndcg_at_10': 0})
        for ranked, grades, ids in [(['a', 'a'], {}, ['a', 'b']), (['z'], {}, ['a']),
                                    ([], {'z': 2}, ['a']), ([], {'a': True}, ['a']),
                                    ([], {'a': 3}, ['a']), ([], {}, ['a', 'a'])]:
            with self.assertRaises(ValueError):
                metrics(ranked, grades, ids)


class BoundaryTests(unittest.TestCase):
    def test_metrics_use_hidden_results(self):
        request = copy.deepcopy(REQUEST)
        request['k'] = 1
        request['qrels'][0]['grades'] = [{'document_id': 'b', 'grade': 2}]
        result = answer(request)['results'][0]
        self.assertEqual([r['document_id'] for r in result['ranking']], ['a'])
        self.assertEqual(result['metrics']['recall_at_5'], 1)
        self.assertEqual(result['metrics']['mrr_at_10'], 0.5)
        self.assertAlmostEqual(result['metrics']['ndcg_at_10'], 1 / math.log2(3))

    def test_aggregate_direct_api_limit(self):
        documents = [{'id': 'd' + str(i), 'text': 'a' * 2048} for i in range(32)]
        with self.assertRaises(ValueError):
            rank(documents, 'a', 'overlap')
        # The exact aggregate boundary is schema-valid without ranking a batch.
        request = copy.deepcopy(REQUEST)
        request['documents'] = documents
        request['queries'][0]['text'] = ''
        request['qrels'][0]['grades'] = []
        validate_request(request)
        request['queries'][0]['text'] = 'a'
        with self.assertRaises(ValueError):
            validate_request(request)

    def test_schema_boundary_matrix(self):
        cases = []
        def altered(path, value):
            request = copy.deepcopy(REQUEST)
            target = request
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            cases.append(request)
        for value in ('', 'x' * 33, 'a/b', '\u00e9', 3, True, None):
            altered(('documents', 0, 'id'), value)
        for value in ('a' * 2049, 'a ' * 257, '\ud800', 3):
            altered(('documents', 0, 'text'), value)
        for value in ('a' * 257, 'a ' * 33, '\udfff', None):
            altered(('queries', 0, 'text'), value)
        for value in (-1, 3, True, 1.0, None, float('nan'), float('inf')):
            altered(('qrels', 0, 'grades', 0, 'grade'), value)
        altered(('qrels', 0, 'query_id'), 'missing')
        altered(('qrels', 0, 'grades', 0, 'document_id'), 'missing')
        altered(('documents',), [{'id': 'd' + str(i), 'text': ''} for i in range(65)])
        altered(('queries',), [{'id': 'q' + str(i), 'text': ''} for i in range(37)])
        altered(('qrels', 0, 'grades'), [{'document_id': 'a', 'grade': 1}] * 65)
        altered(('version',), 1.0)
        altered(('ranker',), {})
        for request in cases:
            with self.subTest(request=str(request)[:100]), self.assertRaises(ValueError):
                validate_request(request)
        for level in ('top', 'query', 'qrel', 'grade'):
            bad = copy.deepcopy(REQUEST)
            target = {'top': bad, 'query': bad['queries'][0], 'qrel': bad['qrels'][0],
                      'grade': bad['qrels'][0]['grades'][0]}[level]
            target['unknown'] = 1
            with self.assertRaises(ValueError):
                validate_request(bad)

    def test_valid_schema_boundaries(self):
        request = copy.deepcopy(REQUEST)
        request['documents'][0]['id'] = 'a' * 32
        request['documents'][0]['text'] = 'a' * 2048
        request['queries'][0]['text'] = 'q' * 256
        request['qrels'][0]['grades'] = []
        self.assertEqual(validate_request(request), {'tiny': {}})
        request['documents'][0]['text'] = 'a ' * 256
        request['queries'][0]['text'] = 'q ' * 32
        validate_request(request)

    def test_multiterm_explanations_independent_oracles(self):
        documents = [{'id': 'a', 'text': 'amber blue'}, {'id': 'b', 'text': 'amber amber'}]
        i = 1 + math.log(1.5)
        norm_squared = 1 + i * i
        rows = rank(documents, 'blue amber blue', 'tfidf')
        self.assertEqual([t['term'] for t in rows[0]['matched_terms']], ['amber', 'blue'])
        self.assertAlmostEqual(rows[0]['matched_terms'][0]['contribution'], 1 / norm_squared, places=14)
        self.assertAlmostEqual(rows[0]['matched_terms'][1]['contribution'], i * i / norm_squared, places=14)
        self.assertAlmostEqual(rows[0]['score'], 1, places=14)
        self.assertAlmostEqual(rows[1]['score'], 1 / math.sqrt(norm_squared), places=14)
        rows = rank(documents, 'blue amber', 'bm25')
        self.assertEqual(rows[0]['matched_terms'][0], {'term': 'amber', 'contribution': 0})
        self.assertAlmostEqual(rows[0]['matched_terms'][1]['contribution'], math.log(2), places=14)
        self.assertAlmostEqual(rows[0]['score'], math.log(2), places=14)
        self.assertEqual([r['score'] for r in rank(documents, 'blue amber', 'overlap')], [2, 1])

    def test_equal_length_duplicate_query_and_qrel_ids(self):
        request = copy.deepcopy(REQUEST)
        request['queries'].append({'id': 'other', 'text': 'blue'})
        request['qrels'].append({'query_id': 'other', 'grades': []})
        validate_request(request)
        bad = copy.deepcopy(request)
        bad['queries'][1]['id'] = 'tiny'
        with self.assertRaises(ValueError):
            validate_request(bad)
        bad = copy.deepcopy(request)
        bad['qrels'][1]['query_id'] = 'tiny'
        with self.assertRaises(ValueError):
            validate_request(bad)
