from django import template

register = template.Library()

from calc.models import *

# An upper function that capitalizes word passed to it. We then register the filter using a suitable name.
@register.simple_tag
def show_calculator_tag(user):
    print ('\n args ====',user)
    print ('\n args id ====',user.id)
    filters = {'active': True, 'is_published': True}
    if not user.is_superuser:
        profile_rec = Profile.objects.filter(user=user.id)
        if profile_rec:
            profile_obj = Profile.objects.get(user=user.id)
            calculator_id = profile_obj and profile_obj.calculator_id or False
            calculator_id = calculator_id and calculator_id.id or False
            calculator_id and filters.update({'id' : calculator_id}) or False
    Calculator_rec = CalculatorMaster.objects.filter(**filters).values('id', 'name')
    print('Calculator_rec==',Calculator_rec)
    Calculator_rec_list = Calculator_rec and list(Calculator_rec) or []
    print('\n Calculator_rec_list ====',Calculator_rec_list)
    return Calculator_rec_list

@register.tag(name='set')
def set_var(parser, token):
    """
    {% set some_var = '123' %}
    """
    parts = token.split_contents()
    if len(parts) < 4:
        raise template.TemplateSyntaxError("'set' tag must be of the form: {% set <var_name> = <var_value> %}")

    return SetVarNode(parts[1], parts[3])