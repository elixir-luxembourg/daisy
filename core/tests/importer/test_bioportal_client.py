import urllib.request, urllib.error, urllib.parse
import json
import pytest

REST_URL = "http://data.bioontology.org"
API_KEY = ""


def get_json(url):
    opener = urllib.request.build_opener()
    opener.addheaders = [('Authorization', 'apikey token=' + API_KEY)]
    return json.loads(opener.open(url).read())

@pytest.mark.skip(reason="we currently use local ontologies. However in the future we may switch to bioportal search.")
@pytest.mark.webtest
def test_term_search():
    terms = []
    terms.append("lewy")


    # Do a search for every term
    search_results = []
    for term in terms:
        search_results.append(get_json(REST_URL + "/search?q=" + term)["collection"])

    # Print the results
    for result in search_results:
        print(result)