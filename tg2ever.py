#!/usr/bin/env python3
from pymorphy2 import MorphAnalyzer

def main():
    morph = MorphAnalyzer()
    for word in ["ста", "ли", "стали"]:
        for form in morph.parse(word):
            print("word={} score={} tag={}".format(
                form.word, form.score, str(form.tag)))
            break

if __name__ == "__main__":
    main()
