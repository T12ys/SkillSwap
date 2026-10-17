from django import template

register = template.Library()


@register.inclusion_tag('includes/stars.html')
def stars(value, size='w-4 h-4'):
    if value is None:
        value = 0
    filled_count = round(value)

    star_list = []
    for number in range(1, 6):
        is_filled = number <= filled_count
        star_list.append(is_filled)

    return {'stars': star_list, 'size': size}

