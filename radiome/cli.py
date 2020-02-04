import argparse
import logging
import os
import sys

from radiome import __version__, __author__, __email__
from radiome import pipeline

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Radiome Pipeline Runner')
    parser.add_argument('inputs_dir', help='The directory with the input dataset '
                                           'formatted according to the BIDS standard. '
                                           'Use the format s3://bucket/path/to/bidsdir'
                                           'to read data directly from an S3 bucket.'
                                           ' This may require AWS S3 credentials specified via the'
                                           ' --aws_input_creds or --aws_input_creds_profile option.')
    parser.add_argument('output_dir', help='The directory where the output files should be stored.'
                                           'Use the format s3://bucket/path/to/bidsdir'
                                           'to read data directly from an S3 bucket.'
                                           ' This may require AWS S3 credentials specified via the'
                                           ' --aws_input_creds or --aws_input_creds_profile option.')
    parser.add_argument('--config_file', help='The path for the pipeline config file.', required=True)
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
    parser.add_argument('--version', action='version',
                        version=f'Radiome version: {__version__}, email: {__email__}, author: {__author__}')
    args = parser.parse_args()
    if not os.path.exists(args.config_file):
        logger.error(f"Couldn't find config file {args.config_file}!")
        return 1
    if not os.path.exists(args.inputs_dir) and not args.inputs_dir.lower().startswith("s3://"):
        logger.error(f"Invalid inputs dir {args.inputs_dir}!")
        return 1
    if not os.path.exists(args.output_dir):
        try:
            os.makedirs(args.output_dir)
            logger.info(f"Output dir {args.output_dir} didn't exist, created.")
        except:
            logger.error(f"Invalid output dir {args.output_dir}.")
            return 1
    logger.info('Building pipeline....')
    pipeline.build(args.inputs_dir, args.output_dir, args.config_file, args.participant_label)
    return 0


if __name__ == "__main__":
    sys.exit(main())
