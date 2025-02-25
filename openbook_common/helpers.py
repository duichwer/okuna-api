import os
import tempfile

from django.core.files import File
from langdetect import DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
from django.conf import settings
import urllib
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urlextract import URLExtract
from webpreview import web_preview
from django.utils.translation import ugettext_lazy as _

from openbook_common.utils.model_loaders import get_language_model
from openbook_translation import translation_strategy

# seed the language detector
DetectorFactory.seed = 0


def get_detected_language_code(text):
    try:
        detected_lang = translation_strategy.get_detected_language_code(text)
    except LangDetectException:
        detected_lang = None
    return detected_lang


def get_language_for_text(text):
    language_code = get_detected_language_code(text)
    Language = get_language_model()
    if language_code is not None and Language.objects.filter(code=language_code).exists():
        return Language.objects.get(code=language_code)

    return None


def get_supported_translation_language(language_code):
    Language = get_language_model()
    supported_translation_code = translation_strategy.get_supported_translation_language_code(language_code)

    return Language.objects.get(code=supported_translation_code)


def extract_urls_from_string(text):
    """
    Returns all the raw extracted urls as a list
    If a URL has a scheme, it ensures that it is http/s
    URLs like www. are sanitised in the normalise_url
    """
    text = text.lower()
    extractor = URLExtract(cache_dir=tempfile.gettempdir())
    results = [url for url in extractor.gen_urls(text)]
    for url in results:
        scheme = urlparse(url).scheme
        if scheme and scheme != 'https' and scheme != 'http':
            results.remove(url)

    return results


def make_proxy_image_url(image_url):
    proxy_image_url = settings.PROXY_URL + image_url

    return proxy_image_url


def write_in_memory_file_to_disk(in_memory_file):
    # Write it to disk
    tmp_file = tempfile.mkstemp(suffix=in_memory_file.name)
    tmp_file_path = tmp_file[1]
    tmp_file = open(tmp_file_path, 'wb')
    tmp_file.write(in_memory_file.read())
    tmp_file.seek(0)
    tmp_file.close()
    return tmp_file
