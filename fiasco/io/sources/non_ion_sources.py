"""
Source classes for CHIANTI filetypes not attached to ions
"""
import os

import numpy as np
import astropy.units as u
from astropy.table import Column
import fortranformat
import plasmapy

from ..generic import GenericParser

__all__ = ['AbundParser', 'IoneqParser', 'IpParser']


class AbundParser(GenericParser):
    filetype = 'abund'
    dtypes = [int,float,str]
    units = [None,u.dimensionless_unscaled,None]
    headings = ['Z', 'abundance', 'element']
    descriptions = ['atomic number', 'abundance relative to H', 'element']
    fformat = fortranformat.FortranRecordReader('(I3,F7.3,A5)')

    def __init__(self, abundance_filename, **kwargs):
        super().__init__(abundance_filename, **kwargs)
        self.full_path = os.path.join(self.ascii_dbase_root, 'abundance', self.filename)

    def postprocessor(self, df):
        df['abundance'] = 10.**(df['abundance'] - df['abundance'][df['Z'] == 1])
        # repair missing data
        if df['element'][0] == '':
            col = []
            for atomic_number in df['Z']:
                col.append(plasmapy.atomic.atomic_symbol(int(atomic_number)))
            df['element'] = Column(col) 
        df = super().postprocessor(df)
        return df

    def to_hdf5(self, hf, df):
        dataset_name = os.path.splitext(os.path.basename(self.filename))[0]
        footer = """{}
------------------
{}
""".format(dataset_name, df.meta['footer'])
        for row in df:
            grp_name = '/'.join([row['element'].lower(), 'abundance'])
            if grp_name not in hf:
                grp = hf.create_group(grp_name)
                grp.attrs['footer'] = ''
                grp.attrs['chianti_version'] = df.meta['chianti_version']
            else:
                grp = hf[grp_name]
            grp.attrs['footer'] += footer
            if dataset_name not in grp:
                ds = grp.create_dataset(dataset_name, data=row['abundance'])
                ds.attrs['unit'] = df['abundance'].unit.to_string()
                ds.attrs['description'] = df.meta['descriptions']['abundance']


class IoneqParser(GenericParser):
    filetype = 'ioneq'
    dtypes = [int,int,float,float]
    units = [None,None,u.K,u.dimensionless_unscaled]
    headings = ['Z', 'ion', 'temperature', 'ionization_fraction']
    descriptions = ['atomic number', 'ion', 'temperature', 'ionization fraction']

    def __init__(self, ioneq_filename, **kwargs):
        super().__init__(ioneq_filename, **kwargs)
        self.full_path = os.path.join(self.ascii_dbase_root, 'ioneq', self.filename)
        
    def preprocessor(self, table, line, index):
        if index == 0:
            num_entries = int(line.strip().split()[0])
            self.fformat_temperature = fortranformat.FortranRecordReader('{}F6.2'.format(num_entries))
            self.fformat_ioneq = fortranformat.FortranRecordReader('2I3,{}E10.2'.format(num_entries))
        elif index == 1:
            self.temperature = 10.**np.array(self.fformat_temperature.read(line),dtype=float)
        else:
            line = self.fformat_ioneq.read(line)
            line = line[:2] + [self.temperature, np.array(line[2:], dtype=float)] 
            table.append(line)

    def to_hdf5(self, hf, df):
        dataset_name = os.path.splitext(os.path.basename(self.filename))[0]
        for row in df:
            el = plasmapy.atomic.atomic_symbol(int(row['Z'])).lower()
            ion = int(row['ion'])
            grp_name = '/'.join([el, '{}_{}'.format(el, ion), 'ioneq'])
            if grp_name not in hf:
                grp = hf.create_group(grp_name)
                grp.attrs['footer'] = ''
            else:
                grp = hf[grp_name]
            if dataset_name not in grp:
                sub_grp = grp.create_group(dataset_name)
                sub_grp.attrs['footer'] = df.meta['footer']
                sub_grp.attrs['chianti_version'] = df.meta['chianti_version']
                ds = sub_grp.create_dataset('temperature', data=row['temperature'])
                ds.attrs['unit'] = df['temperature'].unit.to_string()
                ds.attrs['description'] = df.meta['descriptions']['temperature']
                ds = sub_grp.create_dataset('ionization_fraction', data=row['ionization_fraction'])
                ds.attrs['unit'] = df['ionization_fraction'].unit.to_string()
                ds.attrs['description'] = df.meta['descriptions']['ionization_fraction']


class IpParser(GenericParser):
    filetype = 'ip'
    dtypes = [int,int,float]
    units = [None,None,1/u.cm]
    headings = ['Z', 'ion', 'ip']
    descriptions = ['atomic number', 'ion', 'ionization potential']

    def __init__(self, ip_filename, **kwargs):
        super().__init__(ip_filename, **kwargs)
        self.full_path = os.path.join(self.ascii_dbase_root, 'ip', self.filename)

    def to_hdf5(self, hf, df):
        dataset_name = os.path.splitext(os.path.basename(self.filename))[0]
        footer = """{}
------------------
{}
""".format(dataset_name, df.meta['footer'])
        for row in df:
            el = plasmapy.atomic.atomic_symbol(int(row['Z'])).lower()
            ion = int(row['ion'])
            grp_name = '/'.join([el, '{}_{}'.format(el, ion), 'ip'])
            if grp_name not in hf:
                grp = hf.create_group(grp_name)
                grp.attrs['footer'] = ''
                grp.attrs['chianti_version'] = df.meta['chianti_version']
            else:
                grp = hf[grp_name]
            grp.attrs['footer'] += footer
            if dataset_name not in grp:
                ds = grp.create_dataset(dataset_name, data=row['ip'])
                ds.attrs['unit'] = df['ip'].unit.to_string()
                ds.attrs['description'] = df.meta['descriptions']['ip']

