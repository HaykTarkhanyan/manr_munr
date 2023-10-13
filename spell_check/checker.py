import os
import string
import pandas as pd
from config import REFERENCE_LIST_PATH, INPUT_PATH, INPUT_LIST_PATH, WORDS

from datetime import datetime

# read file, remove punctuation and numbers, split into words save to new file
def clean_file(file, out_file):
    with open(file, encoding="utf-8") as f:
        text = f.read()
        text = text.replace('\n', ' ')
        text = text.replace('\t', ' ')
        
        
        for char in text:
            if not char.isalpha() and (char != ' ') and (char not in "աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆև"):
                text = text.replace(char, '')
             
        text = text.lower()
        text = text.split(' ')
        
        text = sorted(list(set(text)))
            
        to_remove = []
        for word in text:
            print(word)
            if word == '': # empty string
                to_remove.append(word)
            if any([word.startswith(i) for i in string.ascii_letters + string.digits]): # starts with english letter or number
                to_remove.append(word)
            if (len(word) == 1) and word not in "ևուէ":
                to_remove.append(word)
            
        for word in text:
            if len(word) == 1:
                to_remove.append(word)

        text = [word for word in text if word not in to_remove]
            
            
        with open(out_file, 'w', encoding="utf-8") as f:
            for word in text:
                f.write(word + '\n')
             

# clean_file(INPUT_PATH, os.path.join("in", 'input_list.txt'))
    
# def add_words_to_list(new_words_file):
#     with open(reference_list_path, encoding="utf-8") as f:
#         WORDS = f.read().split('\n')
#         print(f'we had {len(WORDS)} words')
        
#         new_words = pd.read_csv(new_words_file)
#         new_words = set(new_words['words'])
            
#         print(f'we have {len(new_words)} new words')
#         for word in new_words:
#             if word not in WORDS:
#                 WORDS.append(word)
                
#         WORDS = sorted(WORDS)
#         print(f'we have {len(WORDS)} words now')
        
#         with open(f"ref_new.txt", 'w', encoding="utf-8") as f:
#             for word in WORDS:
#                 f.write(word + '\n')
                
    
# add_words_to_list('words_to_add.csv')


def check_if_2_letters_swapped(word):
    for i in range(len(word)):
        for j in range(i+1, len(word)):
            if word[i] == word[j]:
                continue
            new_word = word[:i] + word[j] + word[i+1:j] + word[i] + word[j+1:]
            if new_word in WORDS:
                return True, new_word
    return False
        
            
def spell_check(file):
    with open(INPUT_LIST_PATH, encoding="utf-8") as f:
        input_words = f.read().split('\n')
    
    input_words = sorted(list(set(input_words)))
    print(f"We have unique {len(input_words)} words in input file")
    
    words = pd.DataFrame(input_words, columns=['words'])
    words["from_dictionary"] = words["words"].isin(WORDS)
    
    words["2 letters swapped"] = words["words"].apply(check_if_2_letters_swapped)
    words["swapped word"] = words["2 letters swapped"].apply(lambda x: x[1] if x else None)
    words["2 letters swapped"] = words["2 letters swapped"].apply(lambda x: x[0] if x else False) 

    mistakes = words[words['from_dictionary'] == False]
    
    mistakes.to_csv(os.path.join("out", 'mistakes.csv'), index=False)

    words.to_csv(os.path.join("out", 'all.csv'), index=False)
    
spell_check(INPUT_LIST_PATH)
    