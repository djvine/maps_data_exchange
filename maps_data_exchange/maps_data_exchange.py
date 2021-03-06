#!/usr/bin/env python
"""
.. module:: maps_data_exchange.py
   :platform: Unix, Windows
   :synopsis: Converts MAPS HDF5 files to Scientific Data Exchange format.

.. moduleauthor:: David Vine <djvine@gmail.com>


""" 

from data_exchange import DataExchangeFile, DataExchangeEntry
import h5py
import argparse
import glob
import ipdb, pdb
import shutil
import scipy as sp
import Tkinter, tkFileDialog
from Tkinter import Entry, Label, LEFT, RIGHT, StringVar
import os

"""
This mapping is used to automate the creation of SDE files from MAPS files.
Syntax: 
    Key - SDE entry
    Value - root, value, units, description, axes, dataset_opts
"""
class h5val(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

class h5att(object):

    def __init__(self, *args, **kwargs):
        self.args = args
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

MAPS_to_SDE_mapping = { 
    # Raw Data
    'exchange_0': {
                'data': {
                        'title': ('exchange_0', 'Raw fluorescence spectra'),
                        'data': ('exchange_0', h5val('/MAPS/mca_arr'), 'counts', h5att('/MAPS/mca_arr','comments'), 'energy:y:x',{'compression': 'gzip', 'compression_opts': 4}),
                        'x_axis': ('exchange_0', h5val('/exchange/x_axis'), 'mm', h5att('/exchange/x_axis','comments')),
                        'y_axis': ('exchange_0', h5val('/exchange/y_axis'), 'mm', h5att('/exchange/y_axis','comments')),
                        'energy': ('exchange_0', h5val('/MAPS/energy'), 'keV', h5att('/MAPS/energy', 'comments')),
                        'scalers': ('exchange_0', h5val('/MAPS/scalers'), h5val('/MAPS/scaler_units'), h5att('/MAPS/scalers', 'comments'), 'scaler:y:x'),
                        'scaler_names': ('exchange_0', h5val('/MAPS/scaler_names'), 'units', h5att('/MAPS/scaler_names', 'comments')),
                        'fit_parameters': ('exchange_0', h5val('/MAPS/energy_calib'), None, h5att('/MAPS/energy_calib', 'comments')),
                        'angle': ('exchange_0', h5val('/MAPS/extra_pvs', (1, 98)), 'degrees')
                },
    },      
    # Analysed Data
    'exchange_1': { 
                'data': {
                        'title': ('exchange_1', h5att('/MAPS/XRF_fits', 'comments') ),
                        'data': ('exchange_1', h5val('/MAPS/XRF_fits'), h5val('/MAPS/channel_units'), h5att('/MAPS/XRF_fits', 'comments'), 'channel:y:x',{'compression': 'gzip', 'compression_opts': 4}), 
                        'x_axis': ('exchange_1', '/exchange/x_axis', 'mm', h5att('/exchange/x_axis','comments')),
                        'y_axis': ('exchange_1', '/exchange/y_axis', 'mm', h5att('/exchange/y_axis','comments')),
                        'channel_names': ('exchange_1', h5val('/MAPS/channel_names'), 'string', h5att('/MAPS/channel_names','comments')), 
                        'channel_units': ('exchange_1', h5val('/MAPS/channel_units'), 'string', h5att('/MAPS/channel_units','comments')),
                        'fit_parameters': ('exchange_1', h5val('/MAPS/XRF_fits_quant'), None,h5att('/MAPS/XRF_fits_quant', 'comments')) 
                },
    },
    'exchange_2': {
                'data': {
                        'title': ('exchange_2', h5att('/MAPS/XRF_roi', 'comments') ),
                        'data': ('exchange_2', h5val('/MAPS/XRF_roi'), h5val('/MAPS/channel_units'), h5att('/MAPS/XRF_roi', 'comments'), 'channel:y:x',{'compression': 'gzip', 'compression_opts': 4}), 
                        'x_axis': ('exchange_2', '/exchange/x_axis', 'mm', h5att('/exchange/x_axis','comments')),
                        'y_axis': ('exchange_2', '/exchange/y_axis', 'mm', h5att('/exchange/y_axis','comments')),
                        'channel_names': ('exchange_2', '/exchange_1/channel_names', 'string', h5att('/MAPS/channel_names','comments')), 
                        'channel_units': ('exchange_2', '/exchange_1/channel_units', 'string', h5att('/MAPS/channel_units','comments')),
                        'fit_parameters': ('exchange_2', h5val('/MAPS/XRF_roi_quant'), None, h5att('/MAPS/XRF_roi_quant', 'comments')),
                },
    },   
    'exchange_3': {
                'data': {
                        'title': ('exchange_3', h5att('/MAPS/XRF_roi_plus', 'comments') ),
                        'data': ('exchange_3', h5val('/MAPS/XRF_roi_plus'), h5val('/MAPS/channel_units'), h5att('/MAPS/XRF_roi_plus', 'comments'), 'channel:y:x',{'compression': 'gzip', 'compression_opts': 4}), 
                        'x_axis': ('exchange_3', '/exchange/x_axis', 'mm', h5att('/exchange/x_axis','comments')),
                        'y_axis': ('exchange_3', '/exchange/y_axis', 'mm', h5att('/exchange/y_axis','comments')),
                        'channel_names': ('exchange_3', '/exchange_1/channel_names', 'string', h5att('/MAPS/channel_names','comments')), 
                        'channel_units': ('exchange_3', '/exchange_1/channel_units', 'string', h5att('/MAPS/channel_units','comments')),
                        'fit_parameters': ('exchange_3', h5val('/MAPS/XRF_roi_plus_quant'), None, h5att('/MAPS/XRF_roi_plus_quant', 'comments')),
                },

    },
    'exchange_4': {
                'data': {
                        'title': ('exchange_4', h5att('/exchange/images', 'comments') ),
                        'data': ('exchange_4', h5val('/exchange/images'), h5val('/exchange/images_units'), h5att('/exchange/images', 'comments'), 'channel:y:x',{'compression': 'gzip', 'compression_opts': 4}), 
                        'x_axis': ('exchange_4', '/exchange/x_axis', 'mm', h5att('/exchange/x_axis','comments')),
                        'y_axis': ('exchange_4', '/exchange/y_axis', 'mm', h5att('/exchange/y_axis','comments')),
                        'images_names': ('exchange_4', h5val('/exchange/images_names'), 'string', h5att('/exchange/images_names','comments')), 
                        'images_units': ('exchange_4', h5val('/exchange/images_units'), 'string', h5att('/exchange/images_units','comments'))
                },
    },
    'instrument': {
                'instrument': {
                        'name': (None, 'XSD/2-ID-E'),
                },
                'amplifier': {
                    'ds_amplifier': (None, h5val('/MAPS/ds_amp'), None, h5att('/MAPS/ds_amp', 'comments')),
                    'us_amplifier': (None, h5val('/MAPS/us_amp'), None, h5att('/MAPS/us_amp', 'comments'))
                }
    }

}


def convert_to_SDE(filename):
    """
    ..function:: convert_to_SDE(filename)

        This function converts a single MAPS created HDF5 file to Scientific Data Exchange format.


        ..param:: filename - the filename of the MAPS hdf5 file to be converted to 
                             Scientific Data Exchange format.


    """
    
    f_maps = h5py.File(filename, mode='r')

    f_dex = DataExchangeFile('/'.join(filename.split('/')[:-1])+'/'+filename.split('/')[-1].split('.')[0]+'_SDE.h5', mode='w')

    for group in MAPS_to_SDE_mapping.keys():

        for entry_type in MAPS_to_SDE_mapping[group].keys():

            for entry in MAPS_to_SDE_mapping[group][entry_type].keys():
                d, kwargs = {}, {}
                # root
                root = MAPS_to_SDE_mapping[group][entry_type][entry][0]
                # value
                if type(MAPS_to_SDE_mapping[group][entry_type][entry][1])==h5val:
                    d['value'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][1].args[0]].value
                    if len(MAPS_to_SDE_mapping[group][entry_type][entry][1].args)>1:
                        d['value'] = d['value'][MAPS_to_SDE_mapping[group][entry_type][entry][1].args[1]]

                elif type(MAPS_to_SDE_mapping[group][entry_type][entry][1])==h5att:
                    d['value'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][1].args[0]].attrs[MAPS_to_SDE_mapping[group][entry_type][entry][1].args[1]]
                else:
                    d['value'] = MAPS_to_SDE_mapping[group][entry_type][entry][1]
                #units
                try:
                    if type(MAPS_to_SDE_mapping[group][entry_type][entry][2])==h5val:
                        d['units'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][2].args[0]].value
                    elif type(MAPS_to_SDE_mapping[group][entry_type][entry][1])==h5att:
                        d['units'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][2].args[0]].attrs[MAPS_to_SDE_mapping[group][entry_type][entry][2].args[1]]
                    else:
                        if MAPS_to_SDE_mapping[group][entry_type][entry][2]: # Could be None
                            d['units'] = MAPS_to_SDE_mapping[group][entry_type][entry][2]
                    #description
                    if type(MAPS_to_SDE_mapping[group][entry_type][entry][3])==h5val:
                        d['description'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][3].args[0]].value
                    elif type(MAPS_to_SDE_mapping[group][entry_type][entry][3])==h5att:
                        d['description'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][3].args[0]].attrs[MAPS_to_SDE_mapping[group][entry_type][entry][3].args[1]]
                    else:
                        d['description'] = f_maps[MAPS_to_SDE_mapping[group][entry_type][entry][3]]
                    #axes
                    d['axes'] = MAPS_to_SDE_mapping[group][entry_type][entry][4]
                    #dataset_opts
                    d['dataset_opts'] = MAPS_to_SDE_mapping[group][entry_type][entry][5]
                except IndexError:
                    pass
                
                if root is None:
                    f_dex.add_entry(
                        getattr(DataExchangeEntry, entry_type)(**{entry: d})
                    )

                else:
                    f_dex.add_entry(
                        getattr(DataExchangeEntry, entry_type)(**{'root': root, entry: d})
                    )
    f_dex.close()
    f_maps.close()



def create_theta_stack(filenames, output_filename):

    shutil.copy(filenames[0], output_filename)
    f_tomo = DataExchangeFile(output_filename, mode='a')
    
    # Stackable datasets
    # I will create a theta stack for every dataset which has a root entry called 'exchange' and 'exchange_N'
    with DataExchangeFile(filenames[0], mode='r') as f_dex:
        stackable_datasets = [dataset for dataset in f_dex.keys() if dataset.find('exchange_')>-1]

    print 'Found {:d} stackable datasets: '.format(len(stackable_datasets)), stackable_datasets

    for dataset in stackable_datasets:
        print 'Adding {:s}'.format(dataset)
        # loop through all files to determine the image sizes that will be stacked.
        angles = {}
        shapes = []
        for filename in filenames:
            f_dex = DataExchangeFile(filename, mode='r')
            angles[f_dex['/exchange_0/angle'].value] = (filename, f_dex['/'.join([dataset, 'data'])].shape)
            shapes.append(f_dex['/'.join([dataset, 'data'])].shape)
            f_dex.close()
        shapes = list(set(shapes))

        print 'Found {:d} different array shapes: '.format(len(shapes)), shapes[0]
        # Find the max array size
        if len(shapes)>1:
            xmin, ymin = 0,0
            for dim in shapes[0]:
                if dim[1]>xmin:
                    xmin=dim[1]
                if dim[2]>ymin:
                    ymin=dim[2]
        else:
            channels, xmin, ymin = shapes[0]
        array_shape = [len(filenames), channels, xmin, ymin]

        
        

        # Need to add the DataExchange entry in non-standard way because arrays are so large they can't
        # be held in memory simultaneously. So I create a dataset with a single array and the resize
        # it to the right shape. Then arrays can be added individually.

    
        try:
            del f_tomo[dataset+'/data']
        except KeyError:
            pass
        if dataset == 'exchange_0':
            try:
                del f_tomo[dataset+'/angle']
            except KeyError:
                pass

        for i_theta, angle in enumerate(sorted(angles.keys(), key=float)):
            print 'Adding angle {:s}'.format(angle)
            with DataExchangeFile(angles[angle][0], mode='r') as f_dex:
                
                if i_theta==0:
                    ashape = list(f_dex[dataset+'/data'].shape)
                    ashape.insert(0,1)
                    entry = DataExchangeEntry.data(
                    root='/'+dataset,
                    data={
                        'value': sp.zeros(ashape), 
                        'units': f_dex['/'.join([dataset, 'data'])].attrs['units'], 
                        'description': f_dex['/'.join([dataset, 'data'])].attrs['description'],
                        'axes': 'angle:'+f_dex['/'.join([dataset, 'data'])].attrs['axes'],
                        'dataset_opts':  {
                                'compression': 'gzip', 
                                'compression_opts': 4,
                                'maxshape': (None, None, None, None)
                                } 
                            },
                    angles={
                        'value': sorted(angles.keys(), key=float),
                        'units': 'degrees',
                        'description': 'Angles at which each projection was acquired.'
                        }
                    )

                    
                    f_tomo.add_entry(entry)
                    f_tomo['/'.join([dataset, 'data'])].resize(tuple(array_shape))

                f_tomo['/'.join([dataset, 'data'])][i_theta,:,:,:] = f_dex[dataset+'/data'].value

    f_tomo.close()

def main():
    """Define the command line options.

    :returns:  int -- the return code.
    :raises: AttributeError, KeyError

    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--convert-file', help="Convert a single MAPS HDF5 to Scientific Data Exchange format", dest='f', action='store')
    parser.add_argument('-d', '--convert-directory', help="Convert a directory of MAPS HDF5 to Scientific Data Exchange format", dest='d', action='store')
    parser.add_argument('-t', '--create-theta-stack', nargs=2, help="Convert a stack of Scientific Data Exchange \
         files to a single (theta stack) file.\nUsage:\n\t./maps_data_exchange -t input_dir output_filename", dest='t', action='store')
    parser.add_argument('-o', '--open-dialog', help='Open a file dialog to specify which files to convert.', dest='o', action='store_true')
    args = parser.parse_args()

    if args.d:
        filenames = [os.path.abspath(filename) for filename in glob.glob(os.path.abspath(args.d)+'/*.h5') if filename.find('SDE')<0]
        print 'Found {:d} files.'.format(len(filenames))
        f_errors = []
        for filename in filenames:
            print 'Converting {:s}'.format(filename)
            try:
                convert_to_SDE(filename)
            except KeyError as detail:
                '\tFAILED: {:s}'.format(detail)
                f_errors.append(filename)
        if len(f_errors)>0:
            print 'Failed converting {:d} files.'.format(len(f_errors))
            for f_error in f_errors:
                print '\t{:s}'.format(f_error)
    elif args.f:
        convert_to_SDE(os.path.abspath(args.f))
    elif args.t:
        if len(args.t)<2:
            print 'Please specify an input diectory and an output filename.'
            return
        filenames = glob.glob(os.path.abspath(args.t[0])+'/*_SDE.h5')
        create_theta_stack(filenames, os.path.abspath(args.t[1]))
    elif args.o:
        root = Tkinter.Tk()
        #root.withdraw()
        filenames = tkFileDialog.askopenfilenames(initialdir=os.path.expanduser('~'), defaultextension='h5', multiple=True, title='Select MAPS HDF5 files to convert to Scientific Data Exchange format.')
        if len(filenames)==0:
            return
        filenames = [os.path.abspath(filename) for filename in filenames if filename.find('SDE')<0]
        f_errors = []
        for filename in filenames:
            print 'Converting {:s}'.format(filename)
            try:
                convert_to_SDE(filename)
            except KeyError as detail:
                '\tFAILED: {:s}'.format(detail)
                f_errors.append(filename)
        if len(f_errors)>0:
            print 'Failed converting {:d} files.'.format(len(f_errors))
            for f_error in f_errors:
                print '\t{:s}'.format(f_error)
        ofilename = StringVar()
        def func(event):
            global output_filename
            output_filename = os.path.abspath('/'.join(filenames[0].split('/')[:-1]))+'/'+E1.get()
            print('Output filename: {:s}'.format(output_filename))
            root.quit()

        root.bind('<Return>', func)
        L1 = Label(root, text="Output Filename")
        L1.pack( side = LEFT)
        E1 = Entry(root, bd =5, textvariable=ofilename)
        E1.pack(side = RIGHT)
        root.mainloop()
        filenames = [filename.split('.')[0]+'_SDE.h5' for filename in filenames]
        create_theta_stack(filenames, output_filename)    


if __name__=='__main__': main()
