from random import randint
import numpy as np


BOS_TOKEN = 'xbos'
FIELD_TOKEN = 'xfld'


class Tokenizer(object):
    """
    Base class for tokenizers
    """
    dimension = 1

    def __init__(self, filepaths, processes=6, parallelism=4, chunks=1, calculate_coverage=True):

        self.filepaths = filepaths
        self.articles = self.read_articles()
        self.processes = processes
        self.parallelism = parallelism
        self.chunks = chunks
        self.calculate_coverage = calculate_coverage


    def get_one_article(self):
        idx = randint(0, len(self.articles) - 1)
        return self.articles[idx]

    def read_articles(self):
        raise NotImplementedError

    def tokenize(self):
        """
        The code in this method should actually be nearly identical for all
        tokenizers. It's not implemented because the actual processing function - which
        will be different - has to be independent of the class
        """
        raise NotImplementedError

    def preprocess(self, word2int=None, vocab_size=30000, min_frequency=2):
        tokenized_texts = self.tokenize()
        print('Tokenized articles!')
        return_word2int = False
        if word2int is None:
            return_word2int = True
            assert vocab_size is not None, "Vocab size must be defined"
            assert min_frequency is not None, "Minimum word frequency must be defined"

            # now, to find the frequency of words
            if self.dimension == 1:
                unique_tokens, count = np.unique(tokenized_texts, return_counts=True)
            elif self.dimension == 2:
                flat_texts = [tok for sublist in tokenized_texts for tok in sublist]
                unique_tokens, count = np.unique(flat_texts, return_counts=True)

            # get the ordered indices
            sort_indices = count.argsort()[::-1]
            sorted_tokens = unique_tokens[sort_indices]
            sorted_counts = count[sort_indices]

            # make sure all my selected vocab has at least min_frequency words
            assert sorted_counts[vocab_size] >= min_frequency

            # we will now add the unknown and padding tokens
            sorted_tokens = np.insert(sorted_tokens, 0, '_unk_')
            sorted_tokens = np.insert(sorted_tokens, 0, '_pad_')

            # word2int
            word2int = {tok: idx for idx, tok in enumerate(sorted_tokens[:(vocab_size + 2)])}

        unknown_int = word2int['_unk_']
        # now, we can turn tw_ar into an array of ints
        if self.dimension == 1:
            tokenized_ints = [word2int.get(tok, unknown_int) for tok in tokenized_texts]
        elif self.dimension == 2:
            tokenized_ints = [[word2int.get(tok, unknown_int) for tok in subtext] for subtext
                              in tokenized_texts]
        if self.calculate_coverage:
            coverage = self.coverage_calculator(tokenized_ints, unknown_int)
            print('Coverage is {} %'.format(coverage * 100))

        if return_word2int: return tokenized_ints, word2int
        else: return tokenized_ints

    def coverage_calculator(self, tokenized_ints, unknown_idx):
        if self.dimension == 1:
            num_known = sum([1 for tok in tokenized_ints if tok != unknown_idx])
            total_toks = len(tokenized_ints)

        elif self.dimension == 2:
            num_known = sum([sum([1 for tok in sublist if tok != unknown_idx])
                                for sublist in tokenized_ints])
            total_toks = sum([len(sublist) for sublist in tokenized_ints])

        return num_known / total_toks
