# -*- coding: utf-8 -*-
# Fielname = sim_data.py

"""
Simulation data class.
Created on 2017-12-19
@author: dongxiaoguang
"""

import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
from mpl_toolkits.mplot3d import Axes3D
from ..attitude import attitude

D2R = math.pi/180

class Sim_data(object):
    '''
    Simulation data
    '''
    def __init__(self, name, description,\
                 units=None, output_units=None,\
                 plottable=True, logx=False, logy=False,\
                 grid='on', legend=None):
        '''
        Set up data properties and plot properties. All data are stored in a dict (or a scalr or
        a numpy array): self.data.
        Each key of this dict corresponds to a set of data. self.data[key] is of size mxn.
        m is the number of samples of this set of data. n is the dimension of this set of data.
        m may vary through different set of data. n must be same for all sets of data.
        Args:
            name: string name of the data
            description: string description of the data
            units: a tuple or list of strings to specify units of data.
                The length of units is the same as columns of each set of data in self.data.
            output_units: a tuple or list of strings to specify units of data when we plot or
                save the data to files. Sim_data.plot and Sim_data.save_to_file will automatically
                convert units if necessary.
                If this is set to None, output_units will be the same as units, and no unit
                conversion is needed.
            logx: plot this data with log scaling on x axis
            logy: plot this data with log scaling on y axis
            grid: if this is not 'off', it will be changed to 'on'
            legend: tuple or list of strings to specify legend of data.
                The length of units is the same as columns of each set of data in self.data.
        '''
        self.name = name
        self.description = description
        # units of self.data
        if units is None:
            self.units = []
        else:
            self.units = list(units)
        # output units should have same length as units
        if output_units is None:
            self.output_units = self.units
        else:
            self.output_units = list(output_units)
            len_in = len(self.units)
            len_out = len(self.output_units)
            if len_in > len_out:
                for i in range(len_out, len_in):
                    self.output_units.append(self.units[i])
            elif len_in < len_out:
                for i in range(len_in, len_out):
                    self.units.append(self.output_units[i])
        self.plottable = plottable
        self.logx = logx
        self.logy = logy
        self.grid = 'on'
        if grid.lower() == 'off':
            self.grid = grid
        self.legend = legend
        '''
        each item in the data should be either scalar or numpy.array of size(n, dim),
        or a dict of the above two, dict keys are like 0, 1, 2, 3, ...
        n is the sample number, dim is a set of data at time tn. For example, accel is nx3,
        att_quat is nx4, allan_t is (n,)
        '''
        self.data = {}

    def add_data(self, data, key=None, units=None):
        '''
        Add data to Sim_data.
        Args:
            data: a scalar, a numpy array or a dict of the above two. If data is a dict, each
                value in it should be of same type (scalr or numpy array), same size and same
                units.
            key: There are more than one set of data, key is an index of data added this time.
                If key is None, data can be a scalr, a numpy array or a dict of the above two.
                If key is a valid dict key, data can be a scalr or a numpy.
            units: Units of the input data. If you know clearly no units convertion is needed, set
                units to None. If you do not know what units are used in the class InsDataMgr,
                you'd better provide the units of the data. Units convertion will be done
                automatically here.
                If data is a scalar, units should be a list of one string to define its unit.
                If data is a numpy of size(m,n), units should be a list of n strings
                to define the units.
                If data is a dict, units should be the same as the above two depending on if
                each value in the dict is a scalr or a numpy array.
        '''
        # units convertion should be done in sim_data.py
        if units is not None:
            units = list(units) # units of Sim_data is a list even if it contains scalars
            if len(units) == len(self.units):
                if units != self.units:
                    # data units are different from units in the manager, need convertion
                    data = convert_unit(data, units, self.units)
            else:
                print(units)
                print(self.units)
                raise ValueError('Units are of different lengths.')
        # add data into the manager
        if key is None:
            self.data = data
        else:
            if not isinstance(self.data, dict):
                self.data = {}
            self.data[key] = data

    def save_to_file(self, data_dir):
        '''
        Save self.data to files.
        Args:
            data_dir: directory for the data files.
        '''
        #### generate header
        # how many columns in each set of data? 0 if scalar
        cols = 0
        if isinstance(self.data, dict):
            for i in self.data:
                if self.data[i].ndim > 1:
                    cols = self.data[i].shape[1]
                break   # each set of data in data should have the same number of columns
        elif isinstance(self.data, np.ndarray):
            if self.data.ndim > 1:
                cols = self.data.shape[1]
        # add the name and unit of each column to header
        header_line = ''
        if cols > 0:    # more than one column
            for i in range(cols):
                # units
                str_unit = ''
                if i < len(self.output_units):
                    str_unit = ' (' + self.output_units[i] + ')'
                # add a column
                if (self.legend is not None) and (cols == len(self.legend)):    # legend available
                    header_line += self.legend[i] + str_unit + ','
                else:                           # legend not available
                    header_line += self.name + '_' + str(i) + str_unit + ','
            # remove the trailing ','
            header_line = header_line[0:-1]
        else:           # only one column
            str_unit = ''
            if len(self.output_units) > 0:
                str_unit = ' (' + self.output_units[0] + ')'
            header_line = self.name + str_unit
        #### save data and header to .csv files
        if isinstance(self.data, dict):
            for i in self.data:
                file_name = data_dir + '//' + self.name + '-' + str(i) + '.csv'
                np.savetxt(file_name,\
                           convert_unit(self.data[i], self.units, self.output_units),\
                           header=header_line, delimiter=',', comments='')
        else:
            file_name = data_dir + '//' + self.name + '.csv'
            np.savetxt(file_name,\
                       convert_unit(self.data, self.units, self.output_units),\
                       header=header_line, delimiter=',', comments='')

    def plot(self, x, key=None, ref=None, plot3d=0, extra_opt=''):
        '''
        Plot self.data[key]
        Args:
            key is a tuple or list of keys
            x: x axis data
            ref: reference data for error plot is in ref.data
            plot3d: 1--3D plot, 2--3D plot projected on xy, xz and yz, otherwise--2D plot
            extra_opt: strings to specify matplotlib properties.
        '''
        if self.plottable:
            if isinstance(self.data, dict):
                self.__plot_dict(x, key, ref, plot3d, extra_opt)
            else:
                self.__plot_array(x, ref, plot3d, extra_opt)

    def __plot_dict(self, x, key, ref=None, plot3d=0, extra_opt=''):
        '''
        self.data is a dict. plot self.data according to key
        Args:
            x: x axis data Sim_data object.
            key: a list of keys to specify what data in self.data is plotted.
                If key is an empty list, plot all keys in self.data
            ref: reference data for error plot is in ref.data
            plot3d: 1--3D plot, 2--3D plot projected on xy, xz and yz, otherwise--2D plot
            extra_opt: strings to specify matplotlib properties.
        '''
        if key == []:
            key = self.data.keys()
        for i in key:
            y_data = self.data[i]
            # x axis
            if isinstance(x.data, dict):
                if not x.data:  # x.data could be an empty dict
                    x_data = None
                else:
                    x_data = x.data[i]
            else:
                x_data = x.data
            # error
            if ref is not None:
                if isinstance(ref.data, dict):
                    ref_data = ref.data[i]
                else:
                    ref_data = ref.data
                try:
                    y_data = y_data - ref_data
                    if self.units == ['rad', 'rad', 'rad']:
                        y_data = y_data % attitude.TWO_PI
                        idx = y_data > math.pi
                        y_data[idx] = y_data[idx] - attitude.TWO_PI
                except:
                    print('ref data shape: ', ref_data.shape)
                    print('simulation data shape: ', y_data.shape)
                    raise ValueError('Check input data ref and self.data dimension.')
            # unit conversion
            y_data = convert_unit(y_data, self.units, self.output_units)
            # plot
            if plot3d == 1:
                plot3d_in_one_figure(y_data,\
                                     title=self.name + '_' + str(i),\
                                     grid=self.grid,\
                                     legend=self.legend,\
                                     extra_opt=extra_opt)
            elif plot3d == 2:
                plot3d_proj_in_one_figure(y_data,\
                                          title=self.name + '_' + str(i),\
                                          grid=self.grid,\
                                          legend=self.legend,\
                                          extra_opt=extra_opt)
            else:
                plot_in_one_figure(x_data, y_data,\
                                   logx=self.logx, logy=self.logy,\
                                   title=self.name + '_' + str(i),\
                                   xlabel=x.name + ' (' + x.output_units[0] + ')',\
                                   ylabel=self.name + ' (' + str(self.output_units) + ')',\
                                   grid=self.grid,\
                                   legend=self.legend,\
                                   extra_opt=extra_opt)

    def __plot_array(self, x, ref=None, plot3d=0, extra_opt=''):
        '''
        self.data is a numpy.array
        Args:
            x: x axis data Sim_data object.
            ref: reference data for error plot is in ref.data
            plot3d: 1--3D plot, 2--3D plot projected on xy, xz and yz, otherwise--2D plot
        '''
        # x axis
        if isinstance(x.data, dict):
            if not x.data:  # x.data could be an empty dict
                x_data = None
            else:
                # randomly choose data of any key
                for i in x.data:
                    x_data = x.data[i]
                    break
        else:
            x_data = x.data
        # error
        y_data = self.data
        if ref is not None:
            try:
                y_data = self.data - ref.data
                if self.units == ['rad', 'rad', 'rad']:
                    y_data = y_data % attitude.TWO_PI
                    idx = y_data > math.pi
                    y_data[idx] = y_data[idx] - attitude.TWO_PI
            except:
                print(ref.shape)
                print(self.data.shape)
                raise ValueError('Check input data ref and self.data dimension.')
        # unit conversion
        y_data = convert_unit(y_data, self.units, self.output_units)
        # plot
        if plot3d == 1:
            plot3d_in_one_figure(y_data,\
                                 title=self.name,\
                                 grid=self.grid,\
                                 legend=self.legend,\
                                 extra_opt=extra_opt)
        elif plot3d == 2:
            plot3d_proj_in_one_figure(y_data,\
                                      title=self.name,\
                                      grid=self.grid,\
                                      legend=self.legend,\
                                      extra_opt=extra_opt)
        else:
            plot_in_one_figure(x_data, y_data,\
                               logx=self.logx, logy=self.logy,\
                               xlabel=x.name + ' (' + x.output_units[0] + ')',\
                               ylabel=self.name + ' (' + str(self.output_units) + ')',\
                               title=self.name,\
                               grid=self.grid,\
                               legend=self.legend,\
                               extra_opt=extra_opt)

def convert_unit(data, src_unit, dst_unit):
    '''
    Unit conversion. Notice not to change values in data
    Args:
        data: convert data units from src_unit to dst_unit. Data should be a scalar,
            a numpy array of size(n,) or (n,m). n is data length, m is data dimension.
        src_unit: a list of unit of the data.
        dst_unit: a list of unit we want to convert the data to.
    Returns:
        x: data after unit conversion.
    '''
    scale = unit_conversion_scale(src_unit, dst_unit)
    # unit conversion
    x = data.copy() # avoid changing values in data
    if isinstance(x, dict):
        for i in x:
            x[i] = convert_unit_ndarray_scalar(x[i], scale)
    else:
        x = convert_unit_ndarray_scalar(x, scale)
    return x

def unit_conversion_scale(src_unit, dst_unit):
    '''
    Calculate unit conversion scale.
    '''
    m = len(dst_unit)
    scale = np.zeros((m,))
    for i in range(m):
        # deg to rad
        if src_unit[i] == 'deg' and dst_unit[i] == 'rad':
            scale[i] = D2R
        elif src_unit[i] == 'deg/s' and dst_unit[i] == 'rad/s':
            scale[i] = D2R
        # rad to deg
        elif src_unit[i] == 'rad' and dst_unit[i] == 'deg':
            scale[i] = 1.0/D2R
        elif src_unit[i] == 'rad/s' and dst_unit[i] == 'deg/s':
            scale[i] = 1.0/D2R
        else:
            pass
            # print('No need or not know how to convert from %s to %s.'% (src_unit, dst_unit))
    return scale

def convert_unit_ndarray_scalar(x, scale):
    '''
    Unit conversion of numpy array or a scalar.
    Args:
        x: convert x units from src_unit to dst_unit. x should be a scalar,
            a numpy array of size(n,) or (n,m). n is x length, m is x dimension.
        scale: 1D numpy array of unit convertion scale. x = x * scale
    Returns:
        x: x after unit conversion.
    '''
    m = scale.shape[0]
    if isinstance(x, np.ndarray):
        if x.ndim == 2:
            for i in range(min(m, x.shape[1])):
                if scale[i] != 0.0:
                    x[:, i] = x[:, i] * scale[i]
        elif x.ndim == 1:
            if scale[0] != 0.0:
                x = x * scale[0]
    elif isinstance(x, (int, float)):
        x = x * scale[0]
    else:
        raise ValueError('Input x should be a scalar, 1D or 2D array, ndim = %s'% x.ndim)
    return x

def plot_in_one_figure(x, y, logx=False, logy=False,\
                       title='Figure', xlabel=None, ylabel=None,\
                       grid='on', legend=None,\
                       extra_opt=''):
    '''
    Create a figure and plot x/y in this figure.
    Args:
        x: x axis data, np.array of size (n,) or (n,1)
        y: y axis data, np.array of size (n,m)
        title: figure title
        xlabel: x axis label
        ylabel: y axis label
        gird: if this is not 'off', it will be changed to 'on'
        legend: tuple or list of strings of length m.
    '''
    # create figure and axis
    fig = plt.figure(title)
    axis = fig.add_subplot(111)
    lines = []
    # if not x data, generate default x data
    if x is None:
        x = np.array(range(y.shape[0]))
    try:
        dim = y.ndim
        if dim == 1:
            if logx and logy:   # loglog
                line, = axis.loglog(x, y, extra_opt)
            elif logx:          # semilogx
                line, = axis.semilogx(x, y, extra_opt)
            elif logy:          # semilogy
                line, = axis.semilogy(x, y, extra_opt)
            else:               # plot
                line, = axis.plot(x, y, extra_opt)
            lines.append(line)
        elif dim == 2:
            for i in range(0, y.shape[1]):
                if logx and logy:   # loglog
                    line, = axis.loglog(x, y[:, i], extra_opt)
                elif logx:          # semilogx
                    line, = axis.semilogx(x, y[:, i], extra_opt)
                elif logy:          # semilogy
                    line, = axis.semilogy(x, y[:, i], extra_opt)
                else:               # plot
                    line, = axis.plot(x, y[:, i], extra_opt)
                lines.append(line)
        else:
            raise ValueError
    except:
        print('x-axis data len: ', x.shape)
        print('y-axis data shape: ', y.shape)
        raise ValueError('Check input data y.')
    # label
    if xlabel is not None:
        plt.xlabel(xlabel)
    if ylabel is not None:
        plt.ylabel(ylabel)
    # legend
    if legend is not None:
        plt.legend(lines, legend)
    # grid
    if grid.lower() != 'off':
        plt.grid()

def plot3d_in_one_figure(y, title='Figure', grid='on', legend=None, extra_opt=''):
    '''
    Create a figure and plot 3d trajectory in this figure.
    Args:
        y: y axis data, np.array of size (n,3)
        title: figure title
        gird: if this is not 'off', it will be changed to 'on'
        legend: tuple or list of strings of length 3.
    '''
    # create figure and axis
    fig = plt.figure(title)
    axis = fig.add_subplot(111, projection='3d', aspect='equal')
    try:
        dim = y.ndim
        if dim == 2:    # y must be an numpy array of size (n,3), dim=2
            if y.shape[1] != 3:
                raise ValueError
            else:
                axis.plot(y[:, 0], y[:, 1], y[:, 2], extra_opt)
        else:
            raise ValueError
    except:
        print(y.shape)
        raise ValueError('Check input data y.')
    # label
    if isinstance(legend, (tuple, list)):
        n = len(legend)
        if n != 3:
            legend = ['x', 'y', 'z']
    else:
        legend = ['x', 'y', 'z']
    axis.set_xlabel(legend[0])
    axis.set_ylabel(legend[1])
    axis.set_zlabel(legend[2])
    # grid
    if grid.lower() != 'off':
        plt.grid()


def plot3d_proj_in_one_figure(y, title='Figure', grid='on', legend=None, extra_opt=''):
    '''
    Create a figure and plot 3d trajectory in this figure.
    Args:
        y: y axis data, np.array of size (n,3)
        title: figure title
        gird: if this is not 'off', it will be changed to 'on'
        legend: tuple or list of strings of length 3.
    '''
    # plot data
    try:
        dim = y.ndim
        if dim == 2:    # y must be an numpy array of size (n,3), dim=2
            if y.shape[1] != 3:
                raise ValueError
            else:
                # check label
                if isinstance(legend, (tuple, list)):
                    n = len(legend)
                    if n != 3:
                        legend = ['x', 'y', 'z']
                else:
                    legend = ['x', 'y', 'z']
                # check grid
                show_grid = False
                if grid.lower() != 'off':
                    show_grid = True
                # create figure and axis
                # xy
                fig = plt.figure(title)
                axis = fig.add_subplot(131, aspect='equal')
                axis.plot(y[:, 0], y[:, 1], extra_opt)
                axis.set_xlabel(legend[0])
                axis.set_ylabel(legend[1])
                axis.grid(show_grid)
                # xz
                axis = fig.add_subplot(132, aspect='equal')
                axis.plot(y[:, 0], y[:, 2], extra_opt)
                axis.set_xlabel(legend[0])
                axis.set_ylabel(legend[2])
                axis.grid(show_grid)
                # yz
                axis = fig.add_subplot(133, aspect='equal')
                axis.plot(y[:, 1], y[:, 2], extra_opt)
                axis.set_xlabel(legend[1])
                axis.set_ylabel(legend[2])
                axis.grid(show_grid)
        else:
            raise ValueError
    except:
        print(y.shape)
        raise ValueError('Check input data y.')
