import os
import string
import pandas as pd
from config import REFERENCE_LIST_PATH

from datetime import datetime

df = pd.read_csv(os.path.join("out", 'mistakes.csv'))

new_words = list(set(df["words"]))

with open(REFERENCE_LIST_PATH, encoding="utf-8") as f:
    WORDS = f.read().split('\n')
    
    print(f'we had {len(WORDS)} words')
    print(f'we have {len(new_words)} new words')
    
    for word in new_words:
        if word not in WORDS:
            WORDS.append(word)
            
    WORDS = sorted(WORDS)
    print(f'we have {len(WORDS)} words now')
    
    file_path = os.path.join("reference", f"reference_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt")
    with open(file_path, 'w', encoding="utf-8") as f:
        for word in WORDS:
            f.write(word + '\n')
            