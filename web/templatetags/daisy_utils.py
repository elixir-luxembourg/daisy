"""
Template tags utils
"""
from typing import Union
from django.template.base import Node
from django.template.defaulttags import register
from django.urls import reverse

from core.models import Dataset, Project, Contract

@register.filter
def get_item(dictionary, key):
    """
    Get a specific key from dictionnary.
    """
    return dictionary.get(key, '')


@register.filter
def un_underscore(item):
    """
    Replace _ per space.
    """
    return item.replace('_', ' ')


@register.filter(is_safe=True)
def form_add_class(field, css_class):
    return field.as_widget(attrs={'class': css_class})


@register.filter
def can_see_protected(user, obj: Union[Project, Contract, Dataset]):
    has_perm = user.can_see_protected(obj)
    print(f"User {user} wants to see protected elements of {obj}: {has_perm}")
    return has_perm

# @register.simple_tag
# def url_replace_facet(request, field, value):

#     query_dict = request.GET.copy()
#     if not 'selected_facets' in query_dict:
#         query_dict.setlist('selected_facets', ['%s:%s' % (field, value)])
#         return  '?' + query_dict.urlencode()

#     selected_facets = query_dict.pop('selected_facets')

#     is_present = -1
#     for index, element in enumerate(selected_facets):
#         try:
#             name, val = element.split(':')
#             if name == field:
#                 is_present = index
#                 break
#         except ValueError:
#             pass
#     if is_present > -1:
#         selected_facets.pop(is_present)
#     elif value:
#         selected_facets.append('%s:%s' % (field, value))

#     query_dict.setlist('selected_facets', selected_facets)
#     return  '?' + query_dict.urlencode()


# @register.simple_tag
# def url_replace(request, field, value):
#     query_dict = request.GET.copy()
#     query_dict[field] = value
#     return  '?' + query_dict.urlencode()


class FacetLinkNode(Node):
    """
    Special template node used for facet links
    url_name: name of the url
    facet_name: name of the facet
    current_facet: the facet that is currently processed
    """

    def __init__(self, url_name, facet_name, current_facet):
        self.url_name = url_name
        self.facet_name = facet_name
        self.current_facet = current_facet

    def process_request(self, request, facet_name, current_facet):
        query_dict = request.GET.copy()
        is_present = -1
        filters = []
        if 'filters' in query_dict:
            filters = query_dict.pop('filters')
            for index, element in enumerate(filters):
                try:
                    name, value = element.split(':')
                    if name == facet_name and value == current_facet[0]:
                        is_present = index
                        break
                except ValueError:
                    pass
        if is_present > -1:
            filters.pop(is_present)
        else:
            filters.append('%s:%s' % (facet_name, current_facet[0]))

        if filters:
            query_dict.setlist('filters', filters)
        return is_present > -1, query_dict

    def render(self, context):
        # resolve variable from the template context
        facet_name = self.facet_name.resolve(context, True)
        current_facet = self.current_facet.resolve(context, True)

        # build query dict and check if current facet is present in the url already
        is_present, query_dict = self.process_request(context['request'], facet_name, current_facet)

        # build the url
        url = reverse(self.url_name.resolve(context, True)) + '?' + query_dict.urlencode(safe='/&:')

        # set icon to use (icon change if facet is present or not)
        icon = 'radio_button_unchecked'
        clazz = ''
        if is_present:
            icon = 'radio_button_checked'
            clazz = 'active'

        return f'<li class="{clazz}"><a href="{url}"><i class="material-icons">{icon}</i><span>{current_facet[0]} ({current_facet[1]})</span></a></li>'


@register.tag
def facetlink(parser, token):
    """{% facetlink  url_name, facet_name, current_facet %}"""
    bits = list(token.split_contents())
    url_name, facet_name, current_facet = bits[1:]
    return FacetLinkNode(
        parser.compile_filter(url_name),
        parser.compile_filter(facet_name),
        parser.compile_filter(current_facet)
    )


class OrderLinkNode(Node):
    """
    Special template node used for order by links
    url_name: name of the url
    field_name: name of the filed to order by
    """

    def __init__(self, url_name, field):
        self.url_name = url_name
        self.field = field

    def process_request(self, request, field_name):
        query_dict = request.GET.copy()
        order_by = []
        is_present = -1
        sorting_desc = False
        if 'order_by' in query_dict:
            order_by = query_dict.pop('order_by')
            for index, element in enumerate(order_by):
                # check if has -
                is_desc = False
                curname = element
                if curname[0] == '-':
                    is_desc = True
                    curname = curname[1:]
                # check if is field name
                if field_name == curname:
                    is_present = index
                    sorting_desc = is_desc
                    break

        # we change the status of the field name (not present -> sort asc -> sort desc -> not present -> ...)
        # and update display and query parameters accordingly

        if is_present > -1:
            icon = 'arrow_drop_up'
            order_by.pop(is_present)
            if not sorting_desc:
                icon = 'arrow_drop_down'
                order_by.append(f'-{field_name}')
        else:
            icon = 'sort'
            order_by.append(field_name)

        query_dict.setlist('order_by', order_by)
        return icon, query_dict

    def render(self, context):
        field = self.field.resolve(context, True)
        field_title, field_name = field
        # build query dict and check if current sorting
        icon, query_dict = self.process_request(context['request'], field_name)

        # build the url
        url = reverse(self.url_name.resolve(context, True)) + '?' + query_dict.urlencode(safe='/&:')

        return f'<a href="{url}"><button type="button" class="btn btn-secondary"><i class="material-icons">{icon}</i>{field_title}</button></a>'


@register.tag
def orderbylink(parser, token):
    """{% orderbylink  url_name, field_name %}"""
    bits = list(token.split_contents())
    url_name, field_name = bits[1:]
    return OrderLinkNode(
        parser.compile_filter(url_name),
        parser.compile_filter(field_name),
    )
