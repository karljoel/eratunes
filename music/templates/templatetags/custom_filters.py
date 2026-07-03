from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary by key"""
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return ''

@register.filter
def get_hour_display(hour):
    """Convert hour number to readable format"""
    hour_map = {
        '00': '12:00 AM - 1:00 AM',
        '01': '1:00 AM - 2:00 AM',
        '02': '2:00 AM - 3:00 AM',
        '03': '3:00 AM - 4:00 AM',
        '04': '4:00 AM - 5:00 AM',
        '05': '5:00 AM - 6:00 AM',
        '06': '6:00 AM - 7:00 AM',
        '07': '7:00 AM - 8:00 AM',
        '08': '8:00 AM - 9:00 AM',
        '09': '9:00 AM - 10:00 AM',
        '10': '10:00 AM - 11:00 AM',
        '11': '11:00 AM - 12:00 PM',
        '12': '12:00 PM - 1:00 PM',
        '13': '1:00 PM - 2:00 PM',
        '14': '2:00 PM - 3:00 PM',
        '15': '3:00 PM - 4:00 PM',
        '16': '4:00 PM - 5:00 PM',
        '17': '5:00 PM - 6:00 PM',
        '18': '6:00 PM - 7:00 PM',
        '19': '7:00 PM - 8:00 PM',
        '20': '8:00 PM - 9:00 PM',
        '21': '9:00 PM - 10:00 PM',
        '22': '10:00 PM - 11:00 PM',
        '23': '11:00 PM - 12:00 AM',
    }
    return hour_map.get(str(hour), f'{hour}:00')

@register.filter
def get_day_display(day_number):
    """Convert day number to day name"""
    day_map = {
        1: 'Sunday',
        2: 'Monday',
        3: 'Tuesday',
        4: 'Wednesday',
        5: 'Thursday',
        6: 'Friday',
        7: 'Saturday',
    }
    return day_map.get(day_number, '')