"""Original bounded lexical ranking and frozen synthetic protocol. No I/O."""
import math

RANKERS = ('overlap', 'tfidf', 'bm25')
STRATA = ('exact', 'noisy', 'mismatch')
SEEDS = (7, 23, 101)
METRICS = ('recall5', 'mrr10', 'ndcg10')
CHECKS = ('dataset_counts', 'unique_ids', 'latent_qrels', 'paired_qrels',
          'generation_repeat', 'ranking_counts', 'ranking_order', 'finite_scores',
          'explanation_sums', 'repeat_equal', 'metric_bounds', 'contract_keys')
ACCOUNTING = {'seed_count': 3, 'documents_per_seed': 48, 'total_documents': 144,
              'queries_per_seed': 36, 'total_queries': 108, 'ranker_count': 3,
              'first_pass_rankings': 324, 'repeat_rankings': 324, 'total_rankings': 648}
TOPICS = (('velora', 'velsig', 'velalias'), ('nimbrel', 'nimsig', 'nimalias'),
          ('tavrik', 'tavsig', 'tavalias'), ('orsune', 'orssig', 'orsalias'),
          ('pelvix', 'pelsig', 'pelalias'), ('zandrel', 'zansig', 'zanalias'),
          ('quorlen', 'quosig', 'quoalias'), ('ivmora', 'ivmsig', 'ivmalias'),
          ('drelune', 'dresig', 'drealias'), ('fensora', 'fensig', 'fenalias'),
          ('ulveth', 'ulvsig', 'ulvalias'), ('karsumi', 'karsig', 'karalias'))
FACETS = ('faca', 'facb', 'facc', 'facd')
ALIASES = ('aliasa', 'aliasb', 'aliasc', 'aliasd')
NEUTRAL = ('mote', 'reed', 'glint', 'spool', 'cairn', 'wisp', 'loom', 'pebble')


def require(condition):
    if not condition:
        raise ValueError('invalid_schema')


def text_ok(value, limit):
    require(type(value) is str and len(value) <= limit)
    require(all(not 0xD800 <= ord(c) <= 0xDFFF for c in value))


def identifier(value):
    text_ok(value, 32)
    require(bool(value) and all('a' <= c <= 'z' or 'A' <= c <= 'Z'
                               or '0' <= c <= '9' or c in '_-' for c in value))


def tokenize(text):
    text_ok(text, 2048)
    result, word = [], ''
    for char in text:
        if 'A' <= char <= 'Z':
            char = chr(ord(char) + 32)
        if 'a' <= char <= 'z' or '0' <= char <= '9':
            word += char
        elif word:
            result.append(word)
            word = ''
    if word:
        result.append(word)
    return result


def validate_documents(documents):
    require(type(documents) is list and 1 <= len(documents) <= 64)
    seen, total = set(), 0
    for doc in documents:
        require(type(doc) is dict and set(doc) == {'id', 'text'})
        identifier(doc['id'])
        require(doc['id'] not in seen)
        seen.add(doc['id'])
        text_ok(doc['text'], 2048)
        total += len(doc['text'])
        require(len(tokenize(doc['text'])) <= 256)
    require(total <= 65536)
    return seen


def validate_grades(grades, ids):
    require(type(grades) is dict and len(grades) <= 64)
    for doc_id, grade in grades.items():
        identifier(doc_id)
        require(doc_id in ids and type(grade) is int and 0 <= grade <= 2)


def validate_request(request):
    require(type(request) is dict and set(request) ==
            {'version', 'documents', 'queries', 'qrels', 'ranker', 'k'})
    require(type(request['version']) is int and request['version'] == 1)
    require(type(request['ranker']) is str and request['ranker'] in RANKERS)
    require(type(request['k']) is int and 1 <= request['k'] <= 10)
    ids = validate_documents(request['documents'])
    queries = request['queries']
    require(type(queries) is list and 1 <= len(queries) <= 36)
    seen, total = set(), sum(len(d['text']) for d in request['documents'])
    for query in queries:
        require(type(query) is dict and set(query) == {'id', 'text'})
        identifier(query['id'])
        require(query['id'] not in seen)
        seen.add(query['id'])
        text_ok(query['text'], 256)
        require(len(tokenize(query['text'])) <= 32)
        total += len(query['text'])
    require(total <= 65536)
    require(type(request['qrels']) is list and len(request['qrels']) == len(queries))
    truth = {}
    for entry in request['qrels']:
        require(type(entry) is dict and set(entry) == {'query_id', 'grades'})
        qid = entry['query_id']
        identifier(qid)
        require(qid in seen and qid not in truth)
        require(type(entry['grades']) is list and len(entry['grades']) <= 64)
        grades = {}
        for row in entry['grades']:
            require(type(row) is dict and set(row) == {'document_id', 'grade'})
            identifier(row['document_id'])
            require(row['document_id'] not in grades)
            grades[row['document_id']] = row['grade']
        validate_grades(grades, ids)
        truth[qid] = grades
    return truth


def rank(documents, query, ranker='bm25', k=10):
    """Return deterministic top-k with actual additive term contributions."""
    validate_documents(documents)
    text_ok(query, 256)
    require(sum(len(d['text']) for d in documents) + len(query) <= 65536)
    qterms = tokenize(query)
    require(len(qterms) <= 32 and type(ranker) is str and ranker in RANKERS)
    require(type(k) is int and 1 <= k <= 10)
    qterms = sorted(set(qterms))
    counts, df, lengths = {}, {}, {}
    for doc in documents:
        tokens = tokenize(doc['text'])
        tf = {}
        for term in tokens:
            tf[term] = tf.get(term, 0) + 1
        counts[doc['id']] = tf
        lengths[doc['id']] = len(tokens)
        for term in sorted(tf):
            df[term] = df.get(term, 0) + 1
    n = len(documents)
    avglen = sum(lengths.values()) / n
    idf = {t: 1 + math.log((n + 1) / (df[t] + 1)) for t in sorted(df)}
    qnorm = math.sqrt(sum(idf[t] ** 2 for t in qterms if t in idf))
    rows = []
    for doc in documents:
        doc_id = doc['id']
        tf = counts[doc_id]
        dnorm = math.sqrt(sum((tf[t] * idf[t]) ** 2 for t in sorted(tf)))
        terms = []
        for term in qterms:
            if term not in tf:
                continue
            if ranker == 'overlap':
                contribution = 1.0
            elif ranker == 'tfidf':
                contribution = ((tf[term] * idf[term] / dnorm) * (idf[term] / qnorm)
                                if dnorm and qnorm else 0.0)
            else:
                contribution = (math.log(n / df[term]) * tf[term] * 2.2 /
                                (tf[term] + 1.2 * (0.25 + 0.75 * lengths[doc_id] / avglen))
                                if avglen else 0.0)
            terms.append({'term': term, 'contribution': contribution})
        score = sum(t['contribution'] for t in terms)
        require(math.isfinite(score) and score >= 0)
        rows.append({'document_id': doc_id, 'score': score, 'matched_terms': terms})
    rows.sort(key=lambda row: (-row['score'], row['document_id']))
    return rows[:k]


def metrics(ranking, grades, document_ids):
    """Measure a unique possibly partial list against complete bounded truth."""
    require(type(document_ids) in (list, tuple, set) and 1 <= len(document_ids) <= 64)
    for doc_id in document_ids:
        identifier(doc_id)
    ids = set(document_ids)
    require(len(ids) == len(document_ids))
    validate_grades(grades, ids)
    require(type(ranking) is list and len(ranking) <= len(ids))
    seen = set()
    for doc_id in ranking:
        identifier(doc_id)
        require(doc_id in ids and doc_id not in seen)
        seen.add(doc_id)
    positive = sum(g > 0 for g in grades.values())
    recall = sum(grades.get(d, 0) > 0 for d in ranking[:5]) / positive if positive else 0.0
    mrr = 0.0
    for index, doc_id in enumerate(ranking[:10], 1):
        if grades.get(doc_id, 0) > 0:
            mrr = 1 / index
            break
    dcg = sum((2 ** grades.get(d, 0) - 1) / math.log2(i + 1)
              for i, d in enumerate(ranking[:10], 1))
    ideal = sum((2 ** g - 1) / math.log2(i + 1)
                for i, g in enumerate(sorted(grades.values(), reverse=True)[:10], 1))
    return {'recall_at_5': recall, 'mrr_at_10': mrr, 'ndcg_at_10': dcg / ideal if ideal else 0.0}


def answer(request):
    truth = validate_request(request)
    ids = [d['id'] for d in request['documents']]
    results = []
    for query in request['queries']:
        rows = rank(request['documents'], query['text'], request['ranker'], 10)
        values = metrics([r['document_id'] for r in rows], truth[query['id']], ids)
        results.append({'query_id': query['id'], 'ranking': rows[:request['k']], 'metrics': values})
    return {'version': 1, 'ranker': request['ranker'], 'results': results}


def doc_id(seed, topic, facet):
    return 'd' + str((17 * (4 * topic + facet) + seed) % 48).zfill(3)


def synthetic(seed):
    """Generate only; never rank. Truth uses latent topic and facet identities."""
    require(type(seed) is int and seed in SEEDS)
    docs, queries, truth = [], [], {}
    for t in range(12):
        for f in range(4):
            length = 16 + (seed + 3 * t + 5 * f) % 9
            tokens = ([TOPICS[t][0]] * (3 + (seed + t + f) % 3) + [FACETS[f]] * 2 +
                      [TOPICS[t][1], 'archive', 'note'] +
                      [TOPICS[(t + 1 + seed % 11) % 12][0]] * ((seed + t + 2 * f) % 3))
            missing = length - len(tokens)
            tokens += [NEUTRAL[(seed + t + f + j) % 8] for j in range(missing)]
            docs.append({'id': doc_id(seed, t, f), 'text': ' '.join(tokens)})
        h = (seed + t) % 4
        grades = {doc_id(seed, t, h): 2, doc_id(seed, t, (h + 1) % 4): 1,
                  doc_id(seed, t, (h + 2) % 4): 1}
        variants = ((TOPICS[t][0], FACETS[h]),
                    (TOPICS[t][0], FACETS[h], TOPICS[(t + 1) % 12][0],
                     TOPICS[(t + 5) % 12][0], TOPICS[(t + 5) % 12][0], 'staticnoise'),
                    (TOPICS[t][2], ALIASES[h]))
        for stratum, words in zip(STRATA, variants):
            qid = 'q' + str(t).zfill(2) + '_' + stratum
            queries.append({'id': qid, 'text': ' '.join(words)})
            truth[qid] = dict(grades)
    docs.sort(key=lambda d: d['id'])
    return docs, queries, truth


def quality_keys():
    return tuple('s' + str(s) + '_' + r + '_' + z + '_' + m
                 for s in SEEDS for r in RANKERS for z in STRATA for m in METRICS)


def evaluate():
    """Admitted production entry only: exactly 324 rankings then 324 repeats."""
    checks = {name: True for name in CHECKS}
    datasets = [synthetic(s) for s in SEEDS]
    first, counters, cells = [], [0, 0], {}
    for seed, data in zip(SEEDS, datasets):
        docs, queries, truth = data
        ids = [d['id'] for d in docs]
        checks['dataset_counts'] &= len(docs) == 48 and len(queries) == 36
        checks['dataset_counts'] &= all(sum(q['id'].endswith('_' + z) for q in queries) == 12 for z in STRATA)
        checks['unique_ids'] &= len(set(ids)) == 48 and len({q['id'] for q in queries}) == 36
        checks['generation_repeat'] &= synthetic(seed) == data
        for t in range(12):
            h = (seed + t) % 4
            expected = {doc_id(seed, t, h): 2, doc_id(seed, t, (h + 1) % 4): 1,
                        doc_id(seed, t, (h + 2) % 4): 1}
            paired = [truth['q' + str(t).zfill(2) + '_' + z] for z in STRATA]
            checks['paired_qrels'] &= paired[0] == paired[1] == paired[2]
            checks['latent_qrels'] &= all(g == expected and sorted(g.values()) == [1, 1, 2]
                                           and set(g) <= set(ids) for g in paired)
    for pass_index in range(2):
        position = 0
        for seed, data in zip(SEEDS, datasets):
            docs, queries, truth = data
            ids = [d['id'] for d in docs]
            for ranker in RANKERS:
                for query in queries:
                    rows = rank(docs, query['text'], ranker, 10)
                    counters[pass_index] += 1
                    ordered = [(-row['score'], row['document_id']) for row in rows]
                    checks['ranking_order'] &= (ordered == sorted(ordered) and len(rows) == 10 and
                                               len({r['document_id'] for r in rows}) == 10 and
                                               all(r['document_id'] in ids for r in rows))
                    for row in rows:
                        checks['finite_scores'] &= math.isfinite(row['score']) and row['score'] >= 0
                        checks['finite_scores'] &= all(math.isfinite(t['contribution']) and t['contribution'] >= 0
                                                       for t in row['matched_terms'])
                        checks['explanation_sums'] &= row['score'] == sum(t['contribution'] for t in row['matched_terms'])
                    if pass_index == 0:
                        first.append(rows)
                        values = metrics([r['document_id'] for r in rows], truth[query['id']], ids)
                        checks['metric_bounds'] &= all(math.isfinite(v) and -1e-12 <= v <= 1 + 1e-12
                                                       for v in values.values())
                        stratum = query['id'].split('_')[1]
                        for short, long in zip(METRICS, ('recall_at_5', 'mrr_at_10', 'ndcg_at_10')):
                            key = 's' + str(seed) + '_' + ranker + '_' + stratum + '_' + short
                            cells.setdefault(key, []).append(values[long])
                    else:
                        checks['repeat_equal'] &= rows == first[position]
                    position += 1
    checks['ranking_counts'] &= counters == [324, 324]
    checks['dataset_counts'] &= all(len(v) == 12 for v in cells.values())
    values = {key: sum(cell) / len(cell) for key, cell in cells.items()}
    checks['metric_bounds'] &= all(math.isfinite(v) and -1e-12 <= v <= 1 + 1e-12 for v in values.values())
    values.update({'seed_count': len(datasets), 'documents_per_seed': len(datasets[0][0]),
                   'total_documents': sum(len(d[0]) for d in datasets), 'queries_per_seed': len(datasets[0][1]),
                   'total_queries': sum(len(d[1]) for d in datasets), 'ranker_count': len(RANKERS),
                   'first_pass_rankings': counters[0], 'repeat_rankings': counters[1], 'total_rankings': sum(counters)})
    checks['contract_keys'] &= (set(values) == set(quality_keys()) | set(ACCOUNTING) and len(values) == 90
                                and all(values[k] == v for k, v in ACCOUNTING.items()) and len(checks) == 12)
    return {'checks': [{'name': k, 'passed': bool(checks[k])} for k in CHECKS], 'metrics': values}
