```
usage: radiome [-h] --config_file CONFIG_FILE [--working_dir WORKING_DIR]
               [--participant_label [PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]]
               [--aws_input_creds_path AWS_INPUT_CREDS_PATH]
               [--aws_input_creds_profile AWS_INPUT_CREDS_PROFILE]
               [--aws_output_creds_path AWS_OUTPUT_CREDS_PATH]
               [--aws_output_creds_profile AWS_OUTPUT_CREDS_PROFILE] [--n_cpus N_CPUS]
               [--mem_mb MEM_MB] [--mem_gb MEM_GB] [--save_working_dir]
               [--disable_file_logging] [--diagnostics] [--enable_bids_validator]
               [--bids_validator_config BIDS_VALIDATOR_CONFIG] [-v]
               bids_dir outputs_dir

Radiome Pipeline Runner

positional arguments:
  bids_dir              The directory with the input dataset formatted according to the BIDS
                        standard. Use the format s3://bucket/path/to/bidsdirto read data
                        directly from an S3 bucket. This may require AWS S3 credentials
                        specified via the --aws_input_creds or --aws_input_creds_profile
                        option.
  outputs_dir           The directory where the output files should be stored.Use the format
                        s3://bucket/path/to/bidsdirto write data directly to an S3 bucket.
                        This may require AWS S3 credentials specified via the
                        --aws_input_creds or --aws_input_creds_profile option.

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        The path for the pipeline config file.
  --working_dir WORKING_DIR
                        The local directory where temporary file and logs reside. If not
                        set,the output dir will be used. If the output dir is an S3
                        bucket,you must provide a local path or a temporary directory will be
                        created.
  --participant_label [PARTICIPANT_LABEL [PARTICIPANT_LABEL ...]]
                        The label of the participant that should be analyzed. The label
                        corresponds to sub-<participant_label> from the BIDS spec (so it does
                        not include "sub-"). If this parameter is not provided all
                        participants should be analyzed. Multiple participants can be
                        specified with a space separated list.
  --aws_input_creds_path AWS_INPUT_CREDS_PATH
                        The Path for credentials for reading from S3. If not provided and s3
                        paths are specified in the data config we will try to access the
                        bucket anonymously use the string "env" to indicate that input
                        credentials should read from the environment. (E.g. when using AWS
                        iam roles).
  --aws_input_creds_profile AWS_INPUT_CREDS_PROFILE
                        The profile name for credentials for writing to S3. If not provided
                        and s3 paths are specified in the output directory we will try to
                        access the bucket anonymously use the string "env" to indicate that
                        output credentials should read from the environment. (E.g. when using
                        AWS iam roles).
  --aws_output_creds_path AWS_OUTPUT_CREDS_PATH
                        The Path for credentials for writing to S3. If not provided and s3
                        paths are specified in the output directory we will try to access the
                        bucket anonymously use the string "env" to indicate that output
                        credentials should read from the environment. (E.g. when using AWS
                        iam roles).
  --aws_output_creds_profile AWS_OUTPUT_CREDS_PROFILE
                        The profile name for credentials for writing to S3. If not provided
                        and s3 paths are specified in the output directory we will try to
                        access the bucket anonymously use the string "env" to indicate that
                        output credentials should read from the environment. (E.g. when using
                        AWS iam roles).
  --n_cpus N_CPUS       Number of execution resources available for the pipeline
  --mem_mb MEM_MB       Amount of RAM available to the pipeline in megabytes. Included for
                        compatibility with BIDS-Apps standard, but mem_gb is preferred
  --mem_gb MEM_GB       Amount of RAM available to the pipeline in gigabytes. if this is
                        specified along with mem_mb, this flag will take precedence.
  --save_working_dir    Save the contents of the working directory.
  --disable_file_logging
                        Disable file logging, this is useful for clusters that have disabled
                        file locking.
  --diagnostics         Enable diagnostics dashboard of execution engine.
  --enable_bids_validator
                        skips bids validation
  --bids_validator_config BIDS_VALIDATOR_CONFIG
                        JSON file specifying configuration of bids-validator: See
                        https://github.com/INCF/bids-validator for more info
  -v, --version         show program's version number and exit
```

