from django.template import Context, Template
from django.test import RequestFactory

from web.templatetags.daisy_utils import clear_filters_url


def render_tag(tag, request, **ctx):
    ctx["request"] = request
    return Template("{% load daisy_utils %}" + tag).render(Context(ctx))


def test_clear_filters_url_drops_filters_keeps_query():
    request = RequestFactory().get("/", {"filters": "kw:cancer", "query": "foo"})

    url = clear_filters_url({"request": request}, "datasets")

    assert "filters" not in url
    assert "query=foo" in url


def test_facetlink_active_renders_check_and_selected_state():
    request = RequestFactory().get("/", {"filters": "kw:cancer"})

    html = render_tag(
        "{% facetlink 'datasets' 'kw' facet %}", request, facet=("cancer", 3)
    )

    assert 'data-lucide="check"' in html
    assert "selected" in html
    assert "cancer" in html


def test_facetlink_inactive_has_no_check():
    request = RequestFactory().get("/")

    html = render_tag(
        "{% facetlink 'datasets' 'kw' facet %}", request, facet=("cancer", 3)
    )

    assert 'data-lucide="check"' not in html
    assert "cancer" in html


def test_orderbylink_defaults_to_sortable_icon():
    request = RequestFactory().get("/")

    html = render_tag(
        "{% orderbylink 'datasets' field %}", request, field=("Title", "title")
    )

    assert 'data-lucide="arrow-up-down"' in html
    assert "Title" in html
