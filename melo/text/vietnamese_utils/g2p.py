"""from https://github.com/keithito/tacotron

Cleaners are transformations that run over the input text at both training and eval time.

Cleaners can be selected by passing a comma-delimited list of cleaner names as the "cleaners"
hyperparameter. Some cleaners are English-specific. You'll typically want to use:
  1. "english_cleaners" for English text
  2. "transliteration_cleaners" for non-English text that can be transliterated to ASCII using
     the Unidecode library (https://pypi.python.org/pypi/Unidecode)
  3. "basic_cleaners" if you do not want to transliterate (in this case, you should also update
     the symbols in symbols.py to match your data).
"""

import logging
import re

import phonemizer
from unidecode import unidecode

# To avoid excessive logging we set the log level of the phonemizer package to Critical
critical_logger = logging.getLogger("phonemizer")
critical_logger.setLevel(logging.CRITICAL)

# Intializing the phonemizer globally significantly reduces the speed
# now the phonemizer is not initialising at every call
# Might be less flexible, but it is much-much faster
global_en_phonemizer = phonemizer.backend.EspeakBackend(
    language="en-us",
    preserve_punctuation=True,
    with_stress=True,
    language_switch="remove-flags",
    logger=critical_logger,
)

global_vi_phonemizer_south = phonemizer.backend.EspeakBackend(
    language="vi-vn-x-south",
    preserve_punctuation=True,
    with_stress=True,
    language_switch="remove-flags",
)
global_vi_phonemizer_north = phonemizer.backend.EspeakBackend(
    language="vi",
    preserve_punctuation=True,
    with_stress=True,
    language_switch="remove-flags",
)
global_vi_phonemizer_central = phonemizer.backend.EspeakBackend(
    language="vi-vn-x-central",
    preserve_punctuation=True,
    with_stress=True,
    language_switch="remove-flags",
)

# Regular expression matching whitespace:
_whitespace_re = re.compile(r"\s+")

_vietnamese_re = r'[A-Za-zÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ0-9\s]'

# List of (regular expression, replacement) pairs for abbreviations:
_abbreviations = [
    (re.compile("\\b%s\\." % x[0], re.IGNORECASE), x[1])
    for x in [
        ("mrs", "misess"),
        ("mr", "mister"),
        ("dr", "doctor"),
        ("st", "saint"),
        ("co", "company"),
        ("jr", "junior"),
        ("maj", "major"),
        ("gen", "general"),
        ("drs", "doctors"),
        ("rev", "reverend"),
        ("lt", "lieutenant"),
        ("hon", "honorable"),
        ("sgt", "sergeant"),
        ("capt", "captain"),
        ("esq", "esquire"),
        ("ltd", "limited"),
        ("col", "colonel"),
        ("ft", "fort"),
    ]
]


def expand_abbreviations(text):
    for regex, replacement in _abbreviations:
        text = re.sub(regex, replacement, text)
    return text


def lowercase(text):
    return text.lower()


# Function to remove non-Vietnamese characters
def remove_non_vietnamese(text):
    try:
        text = re.sub(f'[^{_vietnamese_re}]+', '', text)
    except:
        text = text
    return text


def collapse_whitespace(text):
    return re.sub(_whitespace_re, " ", text)


def convert_to_ascii(text):
    return unidecode(text)


def basic_cleaners(text):
    """Basic pipeline that lowercases and collapses whitespace without transliteration."""
    text = lowercase(text)
    text = collapse_whitespace(text)
    return text


def transliteration_cleaners(text):
    """Pipeline for non-English text that transliterates to ASCII."""
    text = convert_to_ascii(text)
    text = lowercase(text)
    text = collapse_whitespace(text)
    return text


def english_cleaners2(text):
    """Pipeline for English text, including abbreviation expansion. + punctuation + stress"""
    text = convert_to_ascii(text)
    text = lowercase(text)
    text = expand_abbreviations(text)
    phonemes = global_en_phonemizer.phonemize([text], strip=True, njobs=1)[0]
    phonemes = collapse_whitespace(phonemes)
    return phonemes

def vietnamese_cleaners(text):
    """Pipeline for Vietnamese text, including abbreviation expansion. + punctuation + stress"""
    # print("original text: ", text)
    text = remove_non_vietnamese(text)
    # text = convert_to_ascii(text) # remain current vietnamese text
    text = lowercase(text)
    # text = expand_abbreviations(text)
    phonemes = global_vi_phonemizer_south.phonemize([text], strip=True, njobs=1)[0]
    phonemes = collapse_whitespace(phonemes)
    return phonemes