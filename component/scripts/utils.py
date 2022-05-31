from sepal_ui.scripts import utils as su

import ee


@su.need_ee
def to_date(dates):
    """
    transform a date store as (int) number of days since 2018-12-31 to a date in YYYY.ddd
    adapted from https:#gis.stackexchange.com/a/428770/154945 to tackle the GLAD_S2 date format
    """

    reference_year = ee.Number(2018)

    # compute the approximate number of year
    years = dates.add(364).divide(365).floor().add(reference_year)

    # compute a leap year image
    leap_years = ee.Image(
        ee.Array(
            ee.List.sequence(reference_year, 2070)
            .map(
                lambda y: (
                    ee.Date.fromYMD(ee.Number(y).add(1), 1, 1)  # last of year
                    .advance(-1, "day")
                    .getRelative("day", "year")
                    .gt(364)  # got the extra day
                    .multiply(
                        ee.Number(y)
                    )  # return the actual year if a leap year else 0
                )
            )
            .filter(ee.Filter.neq("item", 0))
        )
    )

    # Mask out leap years after the year of the pixel
    # Results in an image where the pixel value represents the number of leap years
    nb_leap_years = leap_years.arrayMask(leap_years.lte(years)).arrayLength(0)

    # adjust the day with the number of leap year
    # and recompute the number of years
    adust_dates = dates.add(nb_leap_years)
    years = adust_dates.add(364).divide(365).floor().add(reference_year)

    # adapt the number of days if the current year is a leap year
    is_leap_year = leap_years.arrayMask(leap_years.eq(years)).arrayLength(0)
    jan_first = (
        years.subtract(reference_year)
        .multiply(365)
        .subtract(364)
        .add(nb_leap_years)
        .add(1)
        .subtract(is_leap_year)
    )
    dates = adust_dates.subtract(jan_first).add(1)
    is_before_leap_year = dates.lte(31 + 29)
    dates_adjustment = is_leap_year.And(is_before_leap_year)  # 1 if leap day else 0
    dates = dates.subtract(dates_adjustment)

    return years.add(dates.divide(1000))
