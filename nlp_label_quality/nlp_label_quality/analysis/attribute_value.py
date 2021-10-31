import spacy.tokens

from nlp_label_quality.analysis.label_utils import preprocess_value
from nlp_label_quality.analysis.sim_matrix import GloVeSimMatrix, SpaCySimMatrix, OpenGloVeSimMatrix, LevenshteinSimMatrix, TfIdfSimMatrix
from nlp_label_quality.analysis.nltk_utils import pos_tag_wordnet, get_nltk_synsets, get_nltk_data

import numpy as np

from typing import Dict, List, Tuple, Union
from nlp_label_quality.analysis.nlp_models import GloVeModel, SpaCyModel
from spacy.tokens import Doc

import time
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


class Attribute:
    """
    Every Attribute gets its own class for easier handling of the data in coming steps
    """
    __id = 0

    def __init__(self, attr: str, values: Dict[str, int], nlp: SpaCyModel, glove: GloVeModel) -> None:
        logger.info(f'Attribute instance {attr} initializing ...')
        self.id: int = Attribute.__id
        self.attr: str = attr
        self.size: int = len(values)
        self.nlp: SpacyModel = nlp
        self.glove: GloVeModel = glove
        self.attr_values: List['AttributeValue'] = self._initialize_attributevalue_classes(values)
        self.matrix_content: Dict[str, List[np.ndarray]] = {}
        Attribute.__id += 1

    def _initialize_attributevalue_classes(self, values: Dict[str, int]) -> List['AttributeValue']:
        """
        Initialize attribute content as AttributeValue classes

        Parameters
        ----------
        values: Dict[str, int]
            all values that are included under this attribute

        Returns
        -------
        attr_values: List['AttributeValue']
            preprocessed values for each individual attribute label
        """
        tic = time.perf_counter()
        attr_values = []
        # attr{values{attr_value, count}}  -> level deeper where attribute is already filtered -> {attr_value, count}
        for attr_value, count in values.items():
            attr_values.append(AttributeValue(self.nlp, self.glove, attr_value, count))
        toc = time.perf_counter()
        logger.info(f'AttributeValue instances were initialized in {toc - tic} seconds')
        return attr_values

    def build_sim_matrix(self, dict_name: str, options: List[str]) -> None:
        """
        IMPLEMENTATION FOR SINGLE OPTIONS
        Initialize sim_matrices as a list containting multiple classes of different Similarity matrix classes

        Parameters
        ----------
        dict_name: str
            key for dict to get correct similarity_matrices back for different analysis purposes
        options: List[List[str]]
            list of options [model, name, attribute to look for, function]
        """
        matrices = []

        sim_model, name, attr_property, function = options
        attr_content = self._get_content(attr_property)

        similarity_matrix_class = self._select_sim_matrix(sim_model, name, attr_content, function)
        matrices.append(similarity_matrix_class.sim_matrix)  # only append the matrix itself

        self.matrix_content[dict_name] = matrices  # save the matrices within the instance

    def build_sim_matrices(self, dict_name: str, options: List[List[str]]) -> None:
        """
        IMPLEMENTATION FOR MULITPLE OPTIONS
        Initialize sim_matrices as a list containting multiple classes of different Similarity matrix classes

        Parameters
        ----------
        dict_name: str
            key for dict to get correct similarity_matrices back for different analysis purposes
        options: List[List[str]]
            list of options [model, name, attribute to look for, function]
        """
        matrices = []

        for i in range(len(options)):
            sim_model, name, attr_property, function = options[i]
            attr_content = self._get_content(attr_property)

            similarity_matrix_class = self._select_sim_matrix(sim_model, name, attr_content, function)
            matrices.append(similarity_matrix_class.sim_matrix)  # only append the matrix itself

        self.matrix_content[dict_name] = matrices  # save the matrices within the instance

    def _get_content(self, attr_property: str = 'glove_tokens') -> Union[List[str], List[List[str]]]:
        """
        Returns all values with the same property from all attri_values under this attribute

        Parameters
        ----------
        attr_property: str
            property to look for (default = tokens)

        Returns
        -------
        return: Union[List[str], List[List[str]]]
            list of values with given property for each attr_value
        """
        return [getattr(value, attr_property) for value in self.attr_values]

    def _select_sim_matrix(self, argument: str,
                           name: str,
                           attr_content: Union[List[str], List[List[str]]],
                           function: str) -> Union[GloVeSimMatrix, OpenGloVeSimMatrix, TfIdfSimMatrix, SpaCySimMatrix, LevenshteinSimMatrix]:
        """
        Select functions to build SimilarityMatrix from dictionary

        Parameters
        ----------
        argument
            key for switch_dict to choose correct function
        name
            name of sim_matrix
        attr_content
            list of values with certain property for each attr_value
        function
            function string to be used later that is used for calculating the sim_matrix

        Returns
        -------
        sim_matrix
            calculated Sim_matrix
        """
        if argument == 'glove':
            return GloVeSimMatrix(name, attr_content, self.glove, function)
        elif argument == 'open':
            return OpenGloVeSimMatrix(name, attr_content, self.glove, function)
        elif argument == 'tfidf':
            return TfIdfSimMatrix(name, attr_content, self.glove, function)
        elif argument == 'spacy':
            return SpaCySimMatrix(name, attr_content, self.nlp, function)
        elif argument == 'leven':
            return LevenshteinSimMatrix(name, attr_content, '_', '_')
        else:
            logger.error('Invalid option for SimilarityMatrix constructor')


class AttributeValue:
    """
    Every AttributeValue is pre-processed while being initialized in this class all collected within an Attribute class

    Parameters
    ----------
    nlp: SpacyModel
        Spacy model
    glp: GloVeModel
        GloVe model
    attr_value: str
        attribute label
    count: int
        occurence of given attr_value in event log
    """
    nltk_pos_tokens: List[List[str]]
    synonyms: Dict[str, List[str]]
    synsets_right_pos: Dict[str, List]
    __id = 0

    # 'Permit submitted by Employee'
    # tokens: ['Permit', 'submitted',...
    # lemmas: ['permit', 'submit',...

    def __init__(self, nlp: SpaCyModel, glove: GloVeModel, attr_value: str, count: int) -> None:
        """
        Initialize each attribute value for easier work on each value
        Normal string is filtered to not contain SpaCy stopwords and words are lemmatized for better comparison
        """
        self.orig_value = attr_value
        self.count = count
        self.processed_value: str = preprocess_value(self.orig_value)

        self.init_nlp(nlp, glove)

        self.id: int = AttributeValue.__id
        AttributeValue.__id += 1

    def init_nlp(self, nlp: SpaCyModel, glove: GloVeModel):
        """
        After syntax updates, the semantic analysis needs information for nlp analysis
        """
        tic = time.perf_counter()
        # prep for spacy
        self.doc = nlp.model(self.processed_value)
        self.spacy_tokens: List[str] = [token.text for token in self.doc if (not token.is_stop) and (not token.is_oov)]
        self.spacy_lemmas: List[str] = [token.lemma_ if token.lemma_ != '-PRON-' else token.lower_ for token in self.doc if (not token.is_oov) and (not token.is_stop)]
        self.pos_tags: List[str] = [token.pos_ for token in self.doc]
        self.dependencies: List[str] = [token.dep_ for token in self.doc]  # not used
        # prep for gensim
        self.glove_tokens: List[str] = [token for token in self.processed_value.split() if token in glove.model]
        # prep for nltk
        self.nltk_pos_tokens = pos_tag_wordnet(self.spacy_tokens)
        self.synsets_right_pos = get_nltk_synsets(self.nltk_pos_tokens)
        self.synonyms, self.antonyms, self.hypernyms = get_nltk_data(self.synsets_right_pos)

        toc = time.perf_counter()
        logger.info(f'AttributeValue \'{self.processed_value}\' was NLP-preprocessed in {toc - tic} seconds')
