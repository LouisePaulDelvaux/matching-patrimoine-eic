# -*- coding: utf-8 -*-
'''
Author: LPaul-Delvaux
Created on 18 may 2015
'''
import ConfigParser

from os import path

from format_careers_eic import format_career_tables, format_dates, imputation_cc
from format_individual_info_eic import format_individual_info
from matching_patrimoine_eic.base.format_careers import aggregate_career_table, career_table_by_time_unit
from matching_patrimoine_eic.base.format_yearly import format_unique_year
from matching_patrimoine_eic.base.load_data import load_data, store_to_hdf
from matching_patrimoine_eic.base.select_data import select_data, select_generation_before_format
from matching_patrimoine_eic.base.stat_describe import describe_individual_info, describe_missing
# from memory_profiler import profile


# @profile(precision=4)
def format_data(time_unit='year', path_storage=False):
    ''' Format datasets to provide 2 datasets 'individus' (with individual information) and 'careers'''
    format_dates()
    individual_info_formated = format_individual_info()
    if path_storage:
        pss_path = path_storage + 'pss.xlsx'
    else:
        pss_path = False
    format_career_tables(pss_path)
    careers_formated = aggregate_career_table()
    career_table = career_table_by_time_unit(careers_formated, time_unit)
    career_table = imputation_cc(career_table)
    assert 'pe200_09' in list(careers_formated['source'])
    data_formated = {'careers': career_table.sort(columns=['noind', 'start_date']),
                     'individus': individual_info_formated}
    assert careers_formated.shape[0] != 0
    assert individual_info_formated.shape[0] != 0
    return data_formated


# @profile(precision=4)
def import_data(path_data, path_storage, datasets_to_import, file_description_path,
                options_selection=None, test=False, describe=False):
    ''' Main function to load EIC data and put it in the appropriate format
    Input data: raw data available for researchers (.dta format)
    Output: a dict containing two tables -> careers (1 row per indiv*year*status) and individus (1 row per indiv)'''
    load_data(path_storage, path_storage, 'storageEIC_2009', file_description_path,
                               datasets_to_import, test=test, ref_table='b100_09')
    if 'first_generation' or 'last_generation' in options_selection:
        first = options_selection.get("first_generation", None)
        last = options_selection.get("last_generation", None)
        select_generation_before_format(first, last, 'b100_09', 'an')
    data = format_data(time_unit='year', path_storage=path_storage)
    data = select_data(data, file_description_path, options_selection)
    if describe:
        describe_individual_info(data['individus'])
        describe_missing(data, 'sal_brut_deplaf')
    return data


# @profile(precision=4)
def build_eic_data(test=False, describe=False, options_selection=dict()):
    config_directory = path.normpath(path.join(path.dirname(__file__), '..', '..'))
    config = ConfigParser.ConfigParser()
    config.readfp(open(config_directory + '//config.ini'))
    all_options = dict(config.items('EIC'))
    path_data = all_options.get('path_data')
    path_storage = all_options.get('path_storage')
    file_description_path = path_storage + all_options.get('file_description_name')
    datasets = dict([(generic[:-6], name) for generic, name in all_options.iteritems() if generic[-5:] == 'table'])
    data = import_data(path_data, path_storage, datasets, file_description_path,
                       options_selection, test=test, describe=describe)
    data = format_unique_year(data, datasets, option={'complementary': True})
    file_storage_path = path_storage + 'final_eic.h5'
    store_to_hdf(data,file_storage_path)
    return data

if __name__ == '__main__':
    import time
    print "Début"
    t0 = time.time()
    data = build_eic_data(test=True, options_selection=dict(complete_career = True, first_generation = 1942, last_generation = 1958))
    t1 = time.time()
    print '\n Time for importing data {}s.'.format('%.2f' % (t1 - t0))
    # import cProfile
    # command = """import_data(path_data, path_storage, datasets_to_import, file_description_path)"""
    # cProfile.runctx(command, globals(), locals(), filename="OpenGLContext.profile")
