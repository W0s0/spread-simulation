# -*- coding: utf-8 -*-
"""
Created on Tusday February 18 2019
For Microstructure of Financial Markets Assignement.

@author: Nikos Skiadaressis.
"""

from __future__ import (absolute_import, division, print_function, unicode_literals)
import pandas as pd
import os
import datetime as dt

# Libor Table read, Index tranformation to datetime.objects and cleaning for null values.
libor = pd.read_csv(os.path.join(os.getcwd(), 'LIBOR USD-3.csv'), index_col=0)
l = list(libor.index)
for i in range(len(l)):
    l[i] = dt.datetime.strptime(l[i], '%d.%m.%Y').date()
libor.index = l
libor = libor.fillna(0)

def getONlibor(date1, date2):
    """
    Assumes Weekend days are charged with the libor off friday.
    :param date1: The starting period date.
    :param date2: The ending period date.
    :return: The libor coef of the period based on OverNight Libor Rate.
    """
    delta = date2 - date1
    lib = 1
    for i in range(delta.days):
        try:
            date = date1 + dt.timedelta(days=i)
            # Libor is on basis points.
            lib *= (1 + 0.0001 * libor.loc[date, 'ON'])
        # Except for the weekend days.
        except KeyError:
            d = dt.timedelta(days=1)
            while True:
                try:
                    # If libor is not available, use the previous day.
                    lib *= (1 + 0.0001 * libor.loc[date - d, 'ON'])
                    break
                except KeyError:
                    d += dt.timedelta(days=1)
    return lib
