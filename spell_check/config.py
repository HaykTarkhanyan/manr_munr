import os

INPUT_PATH = os.path.join("in", 'input.txt')
INPUT_LIST_PATH = os.path.join("in", 'input_list.txt')
REFERENCE_LIST_PATH = os.path.join("reference", "ref_new.txt")

with open(REFERENCE_LIST_PATH, encoding="utf-8") as f:
    WORDS = f.read().split('\n')