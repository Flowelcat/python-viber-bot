"""This module contains an object that represents a Viber File."""
import datetime
from os.path import basename

from viber import ViberObject

try:
    # python 2.7
    import urlparse
    from urlparse import urlsplit
    from urlparse import urlunsplit
    from urlparse import SplitResult
    from urllib import urlencode
    from urllib import quote
except:
    # python 3.x
    import urllib.parse as urlparse
    from urllib.parse import urlencode
    from urllib.parse import urlsplit
    from urllib.parse import urlunsplit
    from urllib.parse import SplitResult
    from urllib.parse import quote



class File(ViberObject):
    """
    This object represents a file ready to be downloaded. The file can be downloaded with
    :attr:`download`. It is guaranteed that the link will be valid for at least 1 hour.

    Attributes:
        file_url (:obj:`str`): File url without params. Use :attr:`download` to get the file.
        expires (:obj:`datetime.datetime`): Date when link will be unavailable.
        signature (:obj:`str`): Signature of file, needed for :attr:`download`.
        key_pair_id (:obj:`str`): Key pair id of file, needed for :attr:`download`.
        file_name (:obj:`str`): Optional File name
        size (:obj:`str`): Optional. File size.

    Args:
        file_url (:obj:`str`): File url without params. Use :attr:`download` to get the file.
        expires (:obj:`int`): Timestamp in seconds when link will be unavailable.
        signature (:obj:`str`): Signature of file, needed for :attr:`download`.
        key_pair_id (:obj:`str`): Key pair id of file, needed for :attr:`download`.
        file_name (:obj:`str`, optional): Optional File name
        size (:obj:`str`, optional): File size.
        bot (:obj:`viber.Bot`, optional): Bot to use with shortcut method.
        **kwargs (:obj:`dict`): Arbitrary keyword arguments.
    """

    def __init__(self, file_url, expires, signature, key_pair_id, file_name=None, size=None, bot=None, **kwargs):

        # Required
        self.file_url = file_url
        self.expires = datetime.datetime.fromtimestamp(int(expires))
        self.signature = signature
        self.key_pair_id = key_pair_id

        # Optionals
        self.file_name = file_name
        self.size = size

        self.bot = bot

        self._id_attrs = (self.file_path,)

    @classmethod
    def from_url(cls, url, bot, file_name=None, size=None):
        if not url:
            return None

        parsed = urlparse.urlparse(url)
        link = "{scheme}://{domen}{path}".format(scheme=parsed.scheme, domen=parsed.netloc, path=parsed.path)
        data = urlparse.parse_qs(parsed.query)

        return File(link, data["Expires"][0], data["Signature"][0], data["Key-Pair-Id"][0], file_name, size, bot)

    @property
    def file_path(self):
        params = {"Expires": self.expires.timestamp(),
                  "Signature": self.signature,
                  "Key-Pair-Id": self.key_pair_id}

        return "{file_url}?{params}".format(file_url=self.file_url, params=urlencode(params))

    def download(self, custom_path=None, out=None, timeout=None):
        """
        Download this file. By default, the file is saved in the current working directory with its
        original filename as reported by Viber. If a :attr:`custom_path` is supplied, it will be
        saved to that path instead. If :attr:`out` is defined, the file contents will be saved to
        that object using the ``out.write`` method.

        Note:
            :attr:`custom_path` and :attr:`out` are mutually exclusive.

        Args:
            custom_path (:obj:`str`, optional): Custom path.
            out (:obj:`io.BufferedWriter`, optional): A file-like object. Must be opened for
                writing in binary mode, if applicable.
            timeout (:obj:`int` | :obj:`float`, optional): If this value is specified, use it as
                the read timeout from the server (instead of the one specified during creation of
                the connection pool).

        Returns:
            :obj:`str` | :obj:`io.BufferedWriter`: The same object as :attr:`out` if specified.
            Otherwise, returns the filename downloaded to.

        Raises:
            ValueError: If both :attr:`custom_path` and :attr:`out` are passed.

        """
        if custom_path is not None and out is not None:
            raise ValueError('custom_path and out are mutually exclusive')

        # Convert any UTF-8 char into a url encoded ASCII string.
        url = self._get_encoded_url()

        if out:
            buf = self.bot.request.retrieve(url)
            out.write(buf)
            return out
        else:
            if custom_path:
                filename = custom_path
            else:
                filename = basename(self.file_url)

            buf = self.bot.request.retrieve(url, timeout=timeout)
            with open(filename, 'wb') as fobj:
                fobj.write(buf)
            return filename

    def _get_encoded_url(self):
        """Convert any UTF-8 char in :obj:`File.file_path` into a url encoded ASCII string."""
        sres = urlsplit(self.file_path)
        return urlunsplit(SplitResult(sres.scheme, sres.netloc, quote(sres.path), sres.query, sres.fragment))

    def download_as_bytearray(self, buf=None):
        """Download this file and return it as a bytearray.

        Args:
            buf (:obj:`bytearray`, optional): Extend the given bytearray with the downloaded data.

        Returns:
            :obj:`bytearray`: The same object as :attr:`buf` if it was specified. Otherwise a newly
            allocated :obj:`bytearray`.

        """
        if buf is None:
            buf = bytearray()

        buf.extend(self.bot.request.retrieve(self._get_encoded_url()))
        return buf
