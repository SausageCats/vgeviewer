# VGEviewer

VGEviewer is a command line tool to visualize the output data files of [VGE](https://github.com/SausageCats/Py3VGE).

## Preparation

- Python3 >= 3.7
- Pandas
- Matplotlib

## Installation

VGEviewer can be installed with the following commands:

``` bash
$ git clone https://github.com/SausageCats/vgeviewer.git
$ cd vgeviewer
$ python3 setup.py install --user
```

## Usage

Assume that there is a VGE output directory (vge_output) in the current directory.

```bash
$ ls *
vge_output:
vge_jobcommands.csv  vge_joblist.csv  vge_worker_result.csv
```

The vge_output usually contains three files, but two of them can be visualized with VGEviewer; vge_joblist.csv and vge_worker_result.csv.
For example, you can visualize them with the following commands:

```bash
# Draws each column data in the VGE job list file.
# The x-axis of each graph shows the number of data and the y-axis shows the values of each column data.
$ vgeviewer ./vge_output/vge_joblist.csv

# Draws the workload and time of each VGE worker.
# The x-axis of each graph is the rank number of workers, and the y-axis plots the values of the column data job_count and work_time.
$ vgeviewer ./vge_output/vge_worker_result.csv

# Read the csv files in the vge_output directory and visualize the data in each file.
$ vgeviewer ./vge_output
```

### Options

VGEviwer has several options that can be checked by typing `vgeviwer -h`.
Here are some examples of commands with these options.


The following option creates a graph related to the execution time of each job in addition to the column data graph mentioned earlier.
The option works when a job list file is given.

```bash
vgeviewer --add-jobtime ./vge_output/vge_joblist.csv
```

The next option is similar to the previous one, but only creates a graph related to the job execution time.
The option works when a job list file is given.

```bash
vgeviewer --only-jobtime ./vge_output/vge_joblist.csv
```

The following option outputs some information before graphs are displayed.

```bash
vgeviewer --info ./vge_output/vge_joblist.csv
```

The following option prints some information and exits without displaying graphs.

```bash
vgeviewer --no-plot ./vge_output/vge_joblist.csv
```

The following option creates a graph by removing rows with missing values.

```bash
vgeviewer --remove ./vge_output/vge_joblist.csv
```
