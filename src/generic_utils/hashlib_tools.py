"""
Tools for using hashlib
"""
# stdlib
import hashlib

from generic_utils import five


def get_chunked_hash(filelike_obj, chunk_size=8192, hash_func=hashlib.sha256):
    """Iteratively reads chunks from a stream , `filelike_obj` to generate a hash

    :param filelike_obj: a streaming object which has a read() method.
    :type filelike_obj:
    :param chunk_size:
    :type chunk_size: int
    :param hash_func: a hash method in hashlib
    :type hash_func: callable
    :return:
    :rtype:
    """
    filelike_obj.seek(0)
    hasher = hash_func()
    while True:
        data = filelike_obj.read(chunk_size)
        if not data:
            break
        data = five.b(data)
        hasher.update(data)
    return hasher.hexdigest()
