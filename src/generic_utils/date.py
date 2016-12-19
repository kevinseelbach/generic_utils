'''
    Various date related utils.
'''

# stdlib
from datetime import date


def age(birth_date, from_date):
    if ( from_date is None ):
        from_date = date.today()

    try: # raised when birth date is February 29 and the current year is not a leap year
        birthday = birth_date.replace(year=from_date.year)
    except ValueError:
        birthday = birth_date.replace(year=from_date.year, day=birth_date.day - 1)
    if birthday > from_date:
        return from_date.year - birth_date.year - 1
    else:
        return from_date.year - birth_date.year
