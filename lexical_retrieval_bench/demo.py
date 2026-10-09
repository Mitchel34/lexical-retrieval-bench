"""Tiny hand-written example, unrelated to the frozen evaluation corpus."""
import json
from .core import answer

REQUEST = {'version': 1, 'ranker': 'overlap', 'k': 3,
           'documents': [{'id': 'a', 'text': 'amber amber'}, {'id': 'b', 'text': 'blue'}, {'id': 'c', 'text': ''}],
           'queries': [{'id': 'tiny', 'text': 'amber amber absent'}],
           'qrels': [{'query_id': 'tiny', 'grades': [{'document_id': 'a', 'grade': 2}]}]}


def main():
    print(json.dumps(answer(REQUEST), allow_nan=False, indent=2))


if __name__ == '__main__':
    main()
