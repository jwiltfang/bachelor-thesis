from nltk import wordnet as wn
from typing import Dict, List, TypeVar


def get_synonym_matrix(term1_synsets, term2_synsets, threshold=0.7):
    """
    Return (possibly asymmetric) matrix that gives a rough estimate which values could be synonymous;
    synonyms should not be values as strongly as antonyms based on nltk; often antonyms also have a high similarity score
    because they might share the same root hypernym

    Parameters
    ----------
    term1_synsets : Dict[str, List[TypeVar('Synset')]]
        term to compare
    term2_synsets : Dict[str, List['Synset']]
        term to compare
    threshold : float
        threshold value to filter irrelevant scores

    Returns
    -------
    sim_matrix_synsets : np.ndarray
        matrix of shape (len(term1_synsets) x len(term2_synsets))
    """
    sim_matrix = []
    library = {}
    for key1, syn1 in term1_synsets.items():
        sim_list = []
        for key2, syn2 in term2_synsets.items():
            sim_test, max_score = [], 0
            for synset1 in syn1:
                sim_line = []
                for synset2 in syn2:
                    try:
                        if synset1.pos() == synset2.pos():
                            if wn.wup_similarity(synset1, synset2) > threshold or wn.path_similarity(synset1, synset2) > threshold:
                                sim_score = max(wn.wup_similarity(synset1, synset2), wn.path_similarity(synset1, synset2))
                                sim_line.append(sim_score)
                                if sim_score > max_score:
                                    max_score = sim_score
                                    library[f'{key1}:{key2}'] = [synset1, synset2, sim_score]
                    except TypeError:
                        sim_line.append(0)
                try:
                    sim_test.append(max(sim_line))
                except ValueError:
                    sim_test.append(0)
            try:
                sim_list.append(max(sim_test))
            except ValueError:
                sim_list.append(0)
        sim_matrix.append(sim_list)
    sim_matrix_synsets = np.asarray(sim_matrix)
    toc = time.perf_counter()
    logger.info(f'Synonym matrix was found for {term1_synsets.keys()} and {term2_synsets.keys()} in {toc - tic} seconds.')
    return sim_matrix_synsets, library
