from django import template

register = template.Library()

from calc.models import *


# An upper function that capitalizes word passed to it. We then register the filter using a suitable name.
@register.simple_tag
def show_calculator_tag(user):
    filters = {'active': True, 'is_published': True}
    if not user.is_superuser:
        profile_rec = Profile.objects.filter(user=user.id)
        if profile_rec:
            profile_obj = Profile.objects.get(user=user.id)
            calculator_id = profile_obj and profile_obj.calculator_id or False
            calculator_id = calculator_id and calculator_id.id or False
            calculator_id and filters.update({'id': calculator_id}) or False
    Calculator_rec = CalculatorMaster.objects.filter(**filters).values('id', 'name')
    Calculator_rec_list = Calculator_rec and list(Calculator_rec) or []
    return Calculator_rec_list
