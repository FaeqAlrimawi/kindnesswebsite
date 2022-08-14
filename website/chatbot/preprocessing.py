import nltk
from nltk.stem.porter import PorterStemmer # different stemmers exist
import numpy as np

stemmer = PorterStemmer()

def tokenize(sentence):
    if sentence is None:
        return None
    
    return nltk.word_tokenize(sentence)


def stem(word):
   return stemmer.stem(word.lower())

    
def bag_of_words(tokenized_sentence, all_words):
    
    # tokenized_sentence = tokenize(sentence)
    
    tokenized_sentence = [stem(w) for w in tokenized_sentence]
    
    bag = np.zeros(len(all_words), dtype=np.float32)
    
    for idx, w in enumerate(all_words):
        if w in tokenized_sentence:
            bag[idx] = 1.0
            
    
    return bag


# sentence = "hello there"
# all_words = "hi", "hello", "really", "there", "bye"
 
# bag = bag_of_words(sentence, all_words)

# print(bag) 
      
    