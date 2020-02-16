import argparse
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime

import yaml

from radiome import __version__, __author__, __email__
from radiome import pipeline


def print_err(msg: str) -> None:
    print(msg, file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description='Radiome Pipeline Runner')
    parser.add_argument('bids_dir', help='The directory with the input dataset '
                                         'formatted according to the BIDS standard. '
                                         'Use the format s3://bucket/path/to/bidsdir'
                                         'to read data directly from an S3 bucket.'
                                         ' This may require AWS S3 credentials specified via the'
                                         ' --aws_input_creds or --aws_input_creds_profile option.')
    parser.add_argument('outputs_dir', help='The directory where the output files should be stored.'
                                            'Use the format s3://bucket/path/to/bidsdir'
                                            'to write data directly to an S3 bucket.'
                                            ' This may require AWS S3 credentials specified via the'
                                            ' --aws_input_creds or --aws_input_creds_profile option.')
    parser.add_argument('--config_file', help='The path for the pipeline config file.', required=True)
    parser.add_argument('--working_dir', help='The local directory where temporary file and logs reside. If not set,'
                                              'the output dir will be used. If the output dir is an S3 bucket,'
                                              'you must provide a local directory.')
    parser.add_argument('--participant_label', help='The label of the participant'
                                                    ' that should be analyzed. The label '
                                                    'corresponds to sub-<participant_label> from the BIDS spec '
                                                    '(so it does not include "sub-"). If this parameter is not '
                                                    'provided all participants should be analyzed. Multiple '
                                                    'participants can be specified with a space separated list.',
                        nargs="*", type=str)
    parser.add_argument('--aws_input_creds_path', help='The Path for credentials for reading from S3.'
                                                       ' If not provided and s3 paths are specified in the data config'
                                                       ' we will try to access the bucket anonymously'
                                                       ' use the string "env" to indicate that input credentials should'
                                                       ' read from the environment. (E.g. when using AWS iam roles).',
                        default=None)
    parser.add_argument('--aws_input_creds_profile', help='The profile name for credentials for writing to S3.'
                                                          ' If not provided and s3 paths are specified in the output '
                                                          ' directory we will try to access the bucket anonymously'
                                                          ' use the string "env" to indicate that output credentials '
                                                          ' should read from the environment. '
                                                          '(E.g. when using AWS iam roles).',
                        default=None)
    parser.add_argument('--aws_output_creds_path', help='The Path for credentials for writing to S3.'
                                                        ' If not provided and s3 paths are specified in the output'
                                                        ' directory we will try to access the bucket anonymously'
                                                        ' use the string "env" to indicate that output credentials'
                                                        ' should read from the environment. '
                                                        '(E.g. when using AWS iam roles).',
                        default=None)
    parser.add_argument('--aws_output_creds_profile', help='The profile name for credentials for writing to S3.'
                                                           ' If not provided and s3 paths are specified in the output'
                                                           ' directory we will try to access the bucket anonymously'
                                                           ' use the string "env" to indicate that output credentials'
                                                           ' should read from the environment. '
                                                           '(E.g. when using AWS iam roles).',
                        default=None)
    parser.add_argument('--n_cpus', type=int, default=1,
                        help='Number of execution '
                             ' resources available for the pipeline')
    parser.add_argument('--mem_mb', type=float,
                        help='Amount of RAM available to the pipeline in megabytes.'
                             ' Included for compatibility with BIDS-Apps standard, but mem_gb is preferred')
    parser.add_argument('--mem_gb', type=float,
                        help='Amount of RAM available to the pipeline in gigabytes.'
                             ' if this is specified along with mem_mb, this flag will take precedence.')
    parser.add_argument('--save_working_dir', action='store_true',
                        help='Save the contents of the working directory.')
    parser.add_argument('--disable_file_logging', action='store_true',
                        help='Disable file logging, this is useful for clusters that have disabled file locking.')
    parser.add_argument('--skip_bids_validator',
                        help='skips bids validation',
                        action='store_false')
    parser.add_argument('--bids_validator_config', help='JSON file specifying configuration of '
                                                        'bids-validator: See https://github.com/INCF/bids-validator '
                                                        'for more info')
    parser.add_argument('--version', action='version',
                        version=f'Radiome version: {__version__}, email: {__email__}, author: {__author__}')
    args = parser.parse_args()
    context = pipeline.Context()
    # Check the config file.
    if not os.path.exists(args.config_file):
        print_err(f"Can't find config file {args.config_file}!")
        return 1
    with open(args.config_file, 'r') as f:
        context.workflow_config = yaml.safe_load(f)

    # Check the input dataset.
    if not args.bids_dir.lower().startswith("s3://") and not os.path.exists(args.bids_dir):
        print_err(f"Invalid inputs dir {args.bids_dir}!")
        return 1
    context.inputs_dir = args.bids_dir

    # Check the output directory.
    if args.outputs_dir.lower().startswith("s3://"):
        if args.working_dir is None:
            print_err("A local working dir must be specified when use an s3 bucket as output!")
            return 1
        else:
            context.outputs_dir = args.outputs_dir
            context.working_dir = args.working_dir
    else:
        if not os.path.exists(args.outputs_dir):
            try:
                os.makedirs(args.outputs_dir)
            except:
                print_err(f"Can't create output dir {args.output_dir}!")
                return 1
        context.outputs_dir = args.outputs_dir
        if args.working_dir is None:
            context.working_dir = f'{args.outputs_dir}/scratch'
        else:
            context.working_dir = args.working_dir
        if not os.path.exists(context.working_dir):
            try:
                os.makedirs(context.working_dir)
            except:
                print_err(f"Can't create output dir {context.working_dir}!")
                return 1

    # Participant label
    context.participant_label = args.participant_label

    # Set up the logging
    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format='%(asctime)s-15s %(levelname)s %(name)s: %(message)s')
    if not args.disable_file_logging:
        file_handler = logging.FileHandler(
            f'{context.working_dir}/{datetime.now().strftime("radiome_%H_%M_%d_%m_%Y.log")}')
        logging.getLogger().addHandler(file_handler)
    console_handler = logging.StreamHandler()
    logging.getLogger().addHandler(console_handler)

    # Set up maximum memory allowed.
    if args.mem_gb:
        context.memory = float(args.mem_gb * 1024)
    elif args.mem_mb:
        context.memory = float(args.mem_mb)
    else:
        context.memory = 6 * 1024

    # Set up max core allowed
    context.n_cpus = int(args.n_cpus)

    # BIDS Validation
    if not args.skip_bids_validator:
        if not shutil.which('bids-validator'):
            print_err('BIDS Validator is not correctly set up in your system!'
                      'Please refer to https://github.com/bids-standard/bids-validator'
                      'Command line version section for more information.')
        commands = ['bids-validator', f'--config {args.bids_validator_config}',
                    context.inputs_dir] if args.bids_validator_config else ['bids-validator', context.inputs_dir]
        completed_process = subprocess.run(commands, capture_output=True, universal_newlines=True)
        if completed_process.returncode != 0:
            print_err('BIDS Validation failed. The error information is:')
            print(completed_process.stdout.splitlines())
        else:
            print('BIDS Validation passed. Continue')

    # Print runtime information
    print('Building the pipeline....')
    print(context)

    pipeline.build(context)
    return 0


if __name__ == "__main__":
    sys.exit(main())
