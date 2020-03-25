### Install Radiome

To install radiome, run this command in your terminal:

```bash
$ pip install radiome
```

You can also install from sources.

Clone the public repository

```bash
$ git clone https://github.com/radiome-lab/radiome.git
```

And install

```
$ python setup.py install
```

### Install Workflow

To build a pipeline in Radiome, you need some workflows.

Install them use pip:

```bash
$ pip install workflow-name
```

Note that some workflows may require specific software packages (e.g. AFNI, ANTs or FSL). You must set up them correctly.

### Create Pipeline Config

You need a config file to invoke the workflows with required parameters and combine various workflows into a data pipeline. Please refer to [pipeline](https://github.com/radiome-lab/radiome/wiki/Config) for more information.

### Run

You are all set now! Prepare image resources and put them in a local directory or an S3 bucket you have access to. Make sure the naming is BIDS-compliant.

Run:

```bash
$ radiome inputs_location outputs_location --config_file pipeline_config_location
```

Outputs will be produced in ```outputs_location/derivatives/{workflow_name}```, and organized based on BIDS standard.