import argparse
import os
import glob
import re
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters  # Suppress warnings


#
# pandas settings
#
register_matplotlib_converters()
pd.options.display.max_columns = 100
#pprint.pprint(dir(pd.options.display))
#pd.options.display.show_dimensions = False
#pd.describe_option()


#
# base class
#
class Viewer:  # {{{
    def __init__(self, path, opts):
        self.df = ''
        self.columns = []
        self.path = path
        self.opts = opts
        self.info_number = 1

        self.__load()

    def print_all_info(self):
        print(f'[File] {self.path}\n')
        self.print_missing_value()

    def print_missing_value(self):
        mis_vals = self.df.isnull().sum().loc[lambda x: x > 0]
        if len(mis_vals):
            self._print(mis_vals, name='count', msg='Columns have missing values')
        else:
            self._print(None, msg='No missing values', only_msg=True)

    def _print(self, df_or_s, name='', msg='', only_msg=False):
        print(f'[{self.info_number}] {msg}')
        self.info_number += 1
        if only_msg:
            print()
            return

        if isinstance(df_or_s, pd.DataFrame):
            info = df_or_s
        elif isinstance(df_or_s, pd.Series):
            info = df_or_s.to_frame(name=name) if name else df_or_s.to_frame()
        else:
            print('[Error] df_or_s is not dataframe or series')
            exit(1)

        print(info)
        print()

    def __load(self):
        self.df = pd.read_csv(self.path)
        if self.opts['remove_mis_val']:
            self.df = self.df.dropna(how='any')
        if len(self.df) == 0:
            print('Empty data file: ' + self.path)
            exit(1)
        self.columns = self.df.columns.values
#}}}


#
# visualize all columns in vge_joblist.csv
#
class ViewerJoblist(Viewer):  # {{{
    def __init__(self, path, opts):
        super().__init__(path, opts)
        self._ini_set_datetime()
        self._ini_set_filename()

    def draw(self, do_plot=True):
        Drawer.plot_columns(self, figshape=(4, 5), figsize=(15.0, 9.0), do_plot=do_plot)
        #Drawer.plot_columns(self, figshape=(4, 5), figsize=(15.0, 9.0), x_idxs=0, y_idxs=list(range(1, 17)), y_excl_idxs=[0], do_plot=do_plot)

    def print_all_info(self):
        super().print_all_info()
        self.print_max_min_datetime()
        self.print_value_count()

    def _ini_set_datetime(self):
        fmt = '%Y-%m-%d %H:%M:%S.%f'
        self.df['sendvgetime'] = pd.to_datetime(self.df['sendvgetime'].replace(r'(.*)\..*$', r'\1', regex=True), format=fmt)
        self.df['start_time'] = pd.to_datetime(self.df['start_time'].replace(r'(.*)\..*$', r'\1', regex=True), format=fmt)
        self.df['finish_time'] = pd.to_datetime(self.df['finish_time'].replace(r'(.*)\..*$', r'\1', regex=True), format=fmt)

    def _ini_set_filename(self):
        # FIXME: how to shorten long file names
        dt_pat = re.compile(r'\.sh\.\d+$')
        self.df['filename'] = self.df['filename'].apply(lambda s: re.sub(dt_pat, '', s)[:10])

    def print_value_count(self):
        if 'status' in self.columns:
            status = self.df['status'].value_counts()
            if len(status) > 0:
                self._print(status, msg='Job status')

        if 'return_code' in self.columns:
            rc_df = self.df['return_code'].dropna()
            rc_df = rc_df.loc[rc_df != 0]
            if len(rc_df) > 0:
                self._print(rc_df, msg='Non-zero return code found')

    def print_max_min_datetime(self):
        if 'sendvgetime' in self.columns and \
           'start_time' in self.columns and \
           'finish_time' in self.columns:
            time_df = self.df[['sendvgetime', 'start_time', 'finish_time']]
            time_df = pd.DataFrame({'min': time_df.min(), 'max': time_df.max()})
            self._print(time_df, msg='Job execution time')
#}}}


#
# visualize workload and working hours of workers
#
class ViewerWorkerResult(Viewer):  # {{{
    def __init__(self, path, opts):
        super().__init__(path, opts)

    def draw(self, do_plot=True):
        Drawer.plot_columns(self, figshape=(1, 2), figsize=(7.5, 4.5), x_idxs=0, y_idxs=[1, 2], y_excl_idxs=[0], do_plot=do_plot)
        #Drawer.plot_columns(self, figshape=(1, 3), figsize=(15.0, 9.0), do_plot=do_plot)
#}}}


#
# visualize elapsed_time of jobs
#
class ViewerJobTime(ViewerJoblist):  # {{{
    def __init__(self, path, opts):
        super().__init__(path, opts)

    def draw(self, do_plot=True):
        Drawer.plot_job_time(self, figsize=(7.5, 4.5), do_plot=do_plot)
#}}}


#
# Drawer
#
class Drawer:  # {{{

    @classmethod
    def plot_columns(
            cls, viewer,
            figshape, figsize=(15.0, 9.0),
            x_idxs=None, y_idxs=None, y_excl_idxs=[],
            do_plot=True):
        """
        figshape   : tuple
        figsize    : tuple
        x_idxs     : int, list, or None
        y_idxs     : list, or None
        y_excl_idxs: list
        do_plot    : bool
        """
        path = viewer.path
        df = viewer.df
        columns = viewer.columns

        n_rows = figshape[0]
        n_cols = figshape[1]
        n_figs = len(columns)

        if not y_idxs:
            y_idxs = list(range(n_figs))
        if isinstance(x_idxs, int):
            x_idxs = [x_idxs] * len(y_idxs)

        marker, linestyle = cls.__create_plt_items(len(df))
        fig = cls.__create_fig(figsize, path)

        ii = -1
        for i in range(n_figs):
            if i in y_excl_idxs:
                continue
            ii += 1
            ax = fig.add_subplot(n_rows, n_cols, ii + 1)
            if x_idxs:
                ax.plot(df[columns[x_idxs[ii]]], df[columns[y_idxs[ii]]], marker=marker, linestyle='-')
            else:
                ax.plot(df[columns[ii]], marker=marker, linestyle='-')
            ax.set_title(columns[i])
            ax.tick_params(labelsize=10)
            ax.grid()
            try:
                ax.ticklabel_format(useOffset=False)  # prevent scientific notation
            except Exception:
                pass

        plt.tight_layout()
        cls.__plot(do_plot)

    @classmethod
    def plot_job_time(cls, viewer, figsize=(7.5, 4.5), do_plot=True):
        path = viewer.path
        df = viewer.df

        marker, linestyle = cls.__create_plt_items(len(df))
        fig = cls.__create_fig(figsize, path)

        ax = fig.add_subplot('111')
        ax.plot(df['sendvgetime'], marker=marker, linestyle=linestyle, label='sendvgetime')
        ax.plot(df['start_time'], marker=marker, linestyle=linestyle, label='start_time')
        ax.plot(df['finish_time'], marker=marker, linestyle=linestyle, label='finish_time')
        ax.set_title('job time')
        ax.tick_params(labelsize=10)
        ax.grid()
        ax.legend(loc='best')

        cls.__plot(do_plot)

    def __create_fig(figsize, path):
        fig = plt.figure(figsize=figsize, dpi=100)
        fig.canvas.set_window_title(path)
        fig.subplots_adjust(left=0.10, bottom=0.1, right=0.95, top=0.95, wspace=0.1, hspace=0.3)
        backend = matplotlib.get_backend()
        px, py = 40, 50
        if backend == 'TkAgg':
            fig.canvas.manager.window.wm_geometry(f'+{px}+{py}')
        #elif backend == 'WXAgg':
        #    fig.canvas.manager.window.SetPosition((px, py))
        #else:
        #    fig.canvas.manager.window.move(px, py)
        return fig

    def __create_plt_items(datasize):
        marker = '.' if(datasize) < 10000 else ''
        linestyle = '-'
        return marker, linestyle

    def __plot(do_plot):
        if do_plot:
            plt.show()
#}}}


#
# parse command lines
#
def parser_command_line():  # {{{
    parser = argparse.ArgumentParser(description='vge output viewer')
    parser.add_argument('path', metavar='path', nargs='+', help='specify vge output csv file or directory')
    parser.add_argument('-i', '--info', action='store_true', help='print some information before creating a graph')
    parser.add_argument('-r', '--remove', action='store_true', help='remove missing values before creating a graph')
    parser.add_argument('-v', '--version', action='version', version='vgeviewer (version 1.0.0)')
    parser.add_argument('--aj', '--add-jobtime', action='store_true', help='add the creation of a graph of job execution time')
    parser.add_argument('--np', '--no-plot', action='store_true', help='print some information and exit')
    parser.add_argument('--oj', '--only-jobtime', action='store_true', help='only plot data of job execution time')

    args = vars(parser.parse_args())

    args['do_plot'] = False if args.pop('np') else True
    args['show_info'] = args.pop('info')
    args['remove_mis_val'] = args.pop('remove')
    args['add_jobtime'] = args.pop('aj')
    args['only_jobtime'] = args.pop('oj')
    # priority
    if args['add_jobtime'] and args['only_jobtime']:
        args['only_jobtime'] = False

    #
    # check if paths exist
    #
    abs_paths = [os.path.abspath(p) for p in args.pop('path')]
    target_paths = list()
    for path in abs_paths:
        if not os.path.exists(path):
            print(f'Path does not exist: {path}')
            exit(1)
        if os.path.isdir(path):
            target_paths.extend(glob.glob(f'{path}/*.csv'))
        elif os.path.isfile(path):
            target_paths.extend([path])
        else:
            print(f'{path} is not file or directory')
            exit(1)
    args['target_paths'] = target_paths

    #
    # determine which class to use by reading the header file
    #
    args['class_names'] = list()
    for path in args['target_paths'][:]:
        with open(path, 'r') as f:
            for line in f:
                header_line = line.strip('\n')
                break
            if re.match('jobid', header_line):
                args['class_names'].append('ViewerJoblist')
            elif re.match('worker_rank', header_line):
                args['class_names'].append('ViewerWorkerResult')
            elif re.match('command', header_line):
                args['target_paths'].remove(path)
            else:
                print(f'[Warning] Header line does not contain jobid, worker_rank, or command in {path}')
                args['target_paths'].remove(path)
    if not args['class_names']:
        print(f'[Error] Target csv file to visualize does not exit')

    #
    # adjust class names and paths if job time will be plotted
    #
    if args['add_jobtime']:
        for i in range(len(args['class_names'])):
            if args['class_names'][i] == 'ViewerJoblist':
                args['target_paths'].append(args['target_paths'][i])
                args['class_names'].append('ViewerJobTime')

    if args['only_jobtime']:
        for i in range(len(args['class_names'])):
            if args['class_names'][i] == 'ViewerJoblist':
                args['class_names'][i] = 'ViewerJobTime'

    return args
#}}}


#
# main
#
#if __name__ == '__main__':  # {{{
args = parser_command_line()
#args = {'do_plot': True, 'show_info': False, 'remove_mis_val': False, 'add_jobtime': False, 'only_jobtime': False, 'target_paths': ['~/work/vgeviwer/vge_output/small.csv'], 'class_names': ['ViewerJoblist']}
#args = {'do_plot': True, 'show_info': False, 'remove_mis_val': False, 'add_jobtime': False, 'only_jobtime': False, 'target_paths': ['~/work/vgeviwer/vge_output/vge_worker_result.csv'], 'class_names': ['ViewerWorkerResult']}
#args = {'do_plot': True, 'show_info': False, 'remove_mis_val': False, 'add_jobtime': False, 'only_jobtime': False, 'target_paths': ['~/work/vgeviwer/vge_output/vge_joblist.csv'], 'class_names': ['ViewerJoblist']}
#args = {'do_plot': True, 'show_info': False, 'remove_mis_val': False, 'add_jobtime': False, 'only_jobtime': False, 'target_paths': ['~/work/vgeviwer/vge_output/small.csv', '~/work/vgeviwer/vge_output/vge_joblist.csv', '~/work/vgeviwer/vge_output/vge_worker_result.csv'], 'class_names': ['ViewerJoblist', 'ViewerJoblist', 'ViewerJoblist', 'ViewerWorkerResult']}

opts = dict(remove_mis_val=args['remove_mis_val'])

last_idx = len(args['target_paths']) - 1
for i in range(last_idx + 1):
    target_path = args['target_paths'][i]
    class_name = args['class_names'][i]

    viewer = eval(f'{class_name}("{target_path}", {opts})')
    if args['do_plot']:
        if args['show_info']:
            viewer.print_all_info()
        viewer.draw(do_plot=(i == last_idx))
    else:
        viewer.print_all_info()
#}}}
