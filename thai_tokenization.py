from __future__ import absolute_import
from __future__ import division
from __future__ import print_function


from bpe_helper import BPE
import sentencepiece as spm

import collections
import unicodedata
import six
import tensorflow as tf


def convert_to_unicode(text):
  """Converts `text` to Unicode (if it's not already), assuming utf-8 input."""
  if six.PY3:
    if isinstance(text, str):
      return text
    elif isinstance(text, bytes):
      return text.decode("utf-8", "ignore")
    else:
      raise ValueError("Unsupported string type: %s" % (type(text)))
  elif six.PY2:
    if isinstance(text, str):
      return text.decode("utf-8", "ignore")
    elif isinstance(text, unicode):
      return text
    else:
      raise ValueError("Unsupported string type: %s" % (type(text)))
  else:
    raise ValueError("Not running on Python2 or Python 3?")


def convert_by_vocab(vocab, items):
  """Converts a sequence of [tokens|ids] using the vocab."""
  output = []
  for item in items:
    output.append(vocab[item])
  return output


def load_vocab(vocab_file):
  """Loads a vocabulary file into a dictionary."""
  vocab = collections.OrderedDict()
  index = 0
  with tf.gfile.GFile(vocab_file, "r") as reader:
    while True:
      token = reader.readline()
      if token.split(): token = token.split()[0] # to support SentencePiece vocab file
      token = convert_to_unicode(token)
      if not token:
        break
      token = token.strip()
      vocab[token] = index
      index += 1
  return vocab


class ThaiTokenizer(object):
  """Tokenizes Thai texts."""
  
  def __init__(self, vocab_file, spm_file):
    self.vocab = load_vocab(vocab_file)
    self.inv_vocab = {v: k for k, v in self.vocab.items()}
    
    self.bpe = BPE(vocab_file)    
    self.s = spm.SentencePieceProcessor()
    self.s.Load(spm_file)

  def tokenize(self, text):
    bpe_tokens = self.bpe.encode(text).split(' ')
    spm_tokens = self.s.EncodeAsPieces(text)
    
    tokens = bpe_tokens if len(bpe_tokens) < len(spm_tokens) else spm_tokens
    
    split_tokens = []
    
    for token in tokens:
      new_token = token
      
      if token.startswith('_') and not token in self.vocab:
        split_tokens.append('_')
        new_token = token[1:]
        
      if not new_token in self.vocab:
        split_tokens.append('[UNK]')
      else:
        split_tokens.append(new_token)

    return split_tokens

  def convert_tokens_to_ids(self, tokens):
    return convert_by_vocab(self.vocab, tokens)

  def convert_ids_to_tokens(self, ids):
    return convert_by_vocab(self.inv_vocab, ids)
