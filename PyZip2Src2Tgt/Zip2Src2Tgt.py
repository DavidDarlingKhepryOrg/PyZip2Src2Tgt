# -*- coding: utf-8 -*-

# ========================================================================
#
# Copyright © 2017 Khepry Quixote
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ========================================================================
#
# This program will convert any text file(s) within a(the) specified
# zip archive(s) matching the specified "zip" and "source" file extensions
# to a(many) target file(s) with a specified "target" file extension. 
#
# ========================================================================

import argparse
import csv
import io
import os
import sys
import time
import zipfile

# used for sorting dictionaries
# by either their keys or values
from operator import itemgetter

# character transformation tuples list used for
# transforming characters from one character to another
# as some analytical tools are unable to handle mixed
# characters, e.g. Unicode and ASCII, during importation

char_xform_tuples_list = []

char_xform_tuples_list.append(('\r\n', ' ')) # carriage-return, line-feed to single space
char_xform_tuples_list.append(('\n', ' ')) # line-feed to single space
char_xform_tuples_list.append(('\t', ' ')) # tab to single space
char_xform_tuples_list.append((u'\x91', ' ')) # diachritic left single quote to single space
char_xform_tuples_list.append((u'\x92', ' ')) # diachritic right single quote to single space
char_xform_tuples_list.append((u'\x93', ' ')) # diachritic left double quote to single space
char_xform_tuples_list.append((u'\x94', ' ')) # diachritic right double quote to single space
char_xform_tuples_list.append((u'\xa0', ' ')) # non-breaking space to single space

# make sure this character transformation is always the last one added! 
char_xform_tuples_list.append(('  ', ' ')) # double-space to single space

# handle incoming parameters,
# pushing their values into the
# args dictionary for later usage

arg_parser = argparse.ArgumentParser(description='Convert text file(s) within zip archive(s) to the target path')

arg_parser.add_argument('--zip_path',
                        type=str,
                        default='~/Desktop/ZIPs/',
                        help='zip file path')
arg_parser.add_argument('--zip_file_extension',
                        type=str,
                        default='.zip',
                        help='zip file extension')

arg_parser.add_argument('--src_path',
                        type=str,
                        default='~/Desktop/CSVs/',
                        help='source file path')
arg_parser.add_argument('--src_file_extension',
                        type=str,
                        default='.csv',
                        help='source file extension')
arg_parser.add_argument('--src_col_delimiter',
                        type=str, default=',',
                        help='source column delimiter')
arg_parser.add_argument('--src_col_quotechar',
                        type=str,
                        default='"',
                        help='source column quote character')

arg_parser.add_argument('--tgt_path',
                        type=str,
                        default='~/Desktop/TSVs/',
                        help='target file path')
arg_parser.add_argument('--tgt_file_basename',
                        type=str,
                        default='FracFocusRegistry_201707',
                        help='target file base name')
arg_parser.add_argument('--tgt_file_append',
                        type=str,
                        default=False,
                        help='target file append')
arg_parser.add_argument('--tgt_file_extension',
                        type=str,
                        default='.tsv',
                        help='target file extension')
arg_parser.add_argument('--tgt_col_delimiter',
                        type=str,
                        default='\t',
                        help='target column delimiter')
arg_parser.add_argument('--tgt_col_quotechar',
                        type=str,
                        default='"',
                        help='target column quote character')

arg_parser.add_argument('--break_after_first_file',
                        type=bool,
                        default=False,
                        help='break after processing first file')
arg_parser.add_argument('--progress_msg_template',
                        type=str,
                        default='{:s}: {:,.0f} rows in {:.2f} secs at {:,.0f} rows/sec',
                        help='process message template')
arg_parser.add_argument('--rows_flush_interval',
                        type=int,
                        default=100000,
                        help='flush rows to files interval')

arg_parser.add_argument('--max_rows_per_file',
                        type=int,
                        default=0,
                        help='maximum rows per file (0=unlimited)')

args = arg_parser.parse_args()


# mainline routine, by default:
#     zip_extension is '.zip'
#     src_extension is '.csv'
#     tgt_extension is '.tsv'        
#     source is comma-delimited and quoted as needed
#     target is tab-delimited and quoted as needed

def main(zip_path,
         src_path,
         tgt_path,
         tgt_file_basename=None,
         tgt_file_append=None,
         zip_file_extension=None,
         src_file_extension=None,
         tgt_file_extension=None,
         src_col_delimiter=None,
         tgt_col_delimiter=None,
         src_col_quotechar=None,
         tgt_col_quotechar=None,
         break_after_first_file=None,
         rows_flush_interval=None,
         progress_msg_template=None,
         max_rows_per_file=None,
         char_xform_tuples_list=None):
    
    # default incoming parameters
    # as needed if they are None
    if src_file_extension is None:
        src_file_extension = args.src_file_extension
    if tgt_file_extension is None:
        tgt_file_extension = args.tgt_file_extension
    if zip_file_extension is None:
        zip_file_extension = args.zip_file_extension
    if src_col_delimiter is None:
        src_col_delimiter = args.src_col_delimiter
    if tgt_col_delimiter is None:
        tgt_col_delimiter = args.tgt_col_delimiter
    if src_col_quotechar is None:
        src_col_quotechar = args.src_col_quotechar
    if tgt_col_quotechar is None:
        tgt_col_quotechar = args.tgt_col_quotechar
    if tgt_file_basename is None:
        tgt_file_basename = args.tgt_file_basename
    if tgt_file_append is None:
        tgt_file_append = args.tgt_file_append
    if break_after_first_file is None:
        break_after_first_file = args.break_after_first_file
    if rows_flush_interval is None:
        rows_flush_interval = args.rows_flush_interval
    if progress_msg_template is None:
        progress_msg_template = args.progress_msg_template
    if max_rows_per_file is None:
        max_rows_per_file = args.max_rows_per_file
    
    if zip_path.startswith('~'):
        zip_path = os.path.expanduser(zip_path)
        
    if not os.path.exists(zip_path):
        os.makedirs(zip_path)
        
    if not os.path.exists(zip_path):
        print('--zip_path not found: %s' % zip_path)
        sys.exit(404)
    
    if src_path.startswith('~'):
        src_path = os.path.expanduser(src_path)
        
    if not os.path.exists(src_path):
        os.makedirs(src_path)
        
    if not os.path.exists(src_path):
        print('--src_path not found: %s' % src_path)
        sys.exit(404)

    if tgt_path.startswith('~'):
        tgt_path = os.path.expanduser(tgt_path)
        
    if not os.path.exists(tgt_path):
        os.makedirs(tgt_path)
        
    if not os.path.exists(tgt_path):
        print('--tgt_path not found: %s' % tgt_path)
        sys.exit(404)

    # dictionary used to hold
    # to hold the filenames found
    # within the specified zip archive
    # for subsequent sorted access via looping        
    filenames = {}
    
    # walk through any files in the zip path
    for root, _dirs, files in os.walk(zip_path):
        # file-by-file
        for file in files:
            # only process zip archives
            if file.lower().endswith(zip_file_extension.lower()):
                first_file = True
                # derive the zip archive's full file path
                zip_file_name = os.path.join(root, file)
                # open the zip archive file
                with io.open(zip_file_name, 'rb') as fh:
                    zh = zipfile.ZipFile(fh)
                    # build up dictionary of file names and date-times
                    # prior to them being sorted and extracted by date-time
                    for info in zh.infolist():
                        filenames[info.filename] = info.date_time
                    # process file names in date-time sort order
                    # so that the data is likely in the same order
                    # from which it was originally split into CSVs
                    for filename in sorted(filenames.items(), key=itemgetter(1)):
                        # derive the temporary file's name
                        tmp_file_name = os.path.join(src_path, filename[0])
                        # extract file from zip archive
                        # into the zip archive's path
                        zh.extract(filename[0], src_path)
                        # sleep 1 second
                        # to allow extract
                        # to close output file
                        time.sleep(1)
                        # if the temporary file exists
                        if os.path.exists(tmp_file_name):
                            # if the temporary file ends with the desired extension
                            if tmp_file_name.lower().endswith(src_file_extension.lower()):
                                # derive the file output mode, either write ('w') or append ('a')
                                file_mode = 'w' if (first_file or tgt_file_append is None) else 'a'
                                # build target file name for output
                                if tgt_file_basename is None:
                                    tgt_file_name = os.path.join(tgt_path,
                                                        os.path.splitext(os.path.basename(tmp_file_name))[0] + tgt_file_extension)
                                else:
                                    tgt_file_name = os.path.join(tgt_path,
                                                        tgt_file_basename + tgt_file_extension)
                                # if it's the first file
                                # or the target file name
                                # is to be different for each
                                # file in the archive's manifest
                                if first_file or tgt_file_basename is None:
                                    # don't bypass the header row
                                    bypass_header_row = False
                                # otherwise
                                else:
                                    # bypass the header row
                                    bypass_header_row = True
                                # convert the source CSV
                                # to the target CSV, with
                                # delimiter and quote char
                                # tweaks as needed
                                src2tgt_file(tmp_file_name,
                                             tgt_file_name,
                                             file_mode,
                                             src_col_delimiter,
                                             tgt_col_delimiter,
                                             src_col_quotechar,
                                             tgt_col_quotechar,
                                             bypass_header_row,
                                             rows_flush_interval,
                                             progress_msg_template,
                                             max_rows_per_file,
                                             char_xform_tuples_list)
                                first_file = False
                                if break_after_first_file:
                                    break
                    # close the
                    # zip archive
                    zh.close()


# source to target CSV file converter routine, by default:

def src2tgt_file(src_file_name,
                 tgt_file_name,
                 tgt_file_mode=None,
                 src_col_delimiter=None,
                 tgt_col_delimiter=None,
                 src_col_quotechar=None,
                 tgt_col_quotechar=None,
                 bypass_header_row=None,
                 rows_flush_interval=None,
                 progress_msg_template=None,
                 max_rows_per_file=None,
                 char_xform_tuples_list=None):
    
    if src_col_delimiter is None:
        src_col_delimiter = args.src_col_delimiter
    if tgt_col_delimiter is None:
        tgt_col_delimiter = args.tgt_col_delimiter
    if src_col_quotechar is None:
        src_col_quotechar = args.src_col_quotechar
    if tgt_col_quotechar is None:
        tgt_col_quotechar = args.tgt_col_quotechar
    if tgt_file_mode is None:
        tgt_file_mode = 'w'
    if bypass_header_row is None:
        bypass_header_row = False
    if rows_flush_interval is None:
        rows_flush_interval = args.rows_flush_interval
    if progress_msg_template is None:
        progress_msg_template = args.progress_msg_template
    if max_rows_per_file is None:
        max_rows_per_file = args.max_rows_per_file
    if char_xform_tuples_list is None:
        char_xform_tuples_list = []
    
    print('')
    print('=============================')
    print('SRC file: %s' % src_file_name)
    print('-----------------------------')
    
    # open the target file for either write or append,
    # depending upon the incoming file_mode value ('w' or 'a')
    with io.open(tgt_file_name, tgt_file_mode, newline='') as tgt_file:
        
        # instantiate a CSV writer
        csv_writer = csv.writer(tgt_file,
                                delimiter=tgt_col_delimiter,
                                quotechar=tgt_col_quotechar,
                                quoting=csv.QUOTE_MINIMAL)
        
        # open the source file for reading
        with io.open(src_file_name, 'r', newline='') as src_file:
            
            # instantiate a CSV reader
            csv_reader = csv.reader(src_file,
                                    delimiter=src_col_delimiter,
                                    quotechar=src_col_quotechar,
                                    quoting=csv.QUOTE_MINIMAL)
        
            rows = 0
            start_time = time.time()
            
            # row-by-row
            for row in csv_reader:
                rows += 1
                # assuming each file has a header row
                if not bypass_header_row or rows > 1:
                    # if character transformations
                    # were specified in the tuples list
                    if len(char_xform_tuples_list) > 0:
                        # for each row column
                        for i in range(len(row)):
                            # character transform by character transform
                            for char_xform_tuple in char_xform_tuples_list:
                                # while any matching characters are found
                                while char_xform_tuple[0] in row[i]:
                                    # transform the matching characters into the specified target characters
                                    row[i] = row[i].replace(char_xform_tuple[0], char_xform_tuple[1]).strip()
                    # output row to CSV writer
                    csv_writer.writerow(row)
                # flush output based on the interval
                if rows % rows_flush_interval == 0:
                    tgt_file.flush()
                    # output a progress message
                    elapsed_time = time.time() - start_time
                    print(progress_msg_template.format(src_file_name,
                                                       rows,
                                                       elapsed_time,
                                                       rows / elapsed_time if elapsed_time > 0 else rows))
                    
                # if max rows per file is not unlimited, i.e. equal to zero
                # and the number of rows exceeds the max rows per file value
                if max_rows_per_file > 0 and rows >= max_rows_per_file:
                    # cease processing this file
                    break
        
        # flush output at the end
        # of the CSV input file
        tgt_file.flush()
        # output a progress message
        elapsed_time = time.time() - start_time
        print(progress_msg_template.format(src_file_name,
                                           rows,
                                           elapsed_time,
                                           rows / elapsed_time if elapsed_time > 0 else rows))


# invoke mainline routine
# with specified arguments
  
if __name__ == "__main__":
    
    main(args.zip_path,
         args.src_path,
         args.tgt_path,
         args.tgt_file_basename,
         args.tgt_file_append,
         args.zip_file_extension,
         args.src_file_extension,
         args.tgt_file_extension,
         args.src_col_delimiter,
         args.tgt_col_delimiter,
         args.src_col_quotechar,
         args.tgt_col_quotechar,
         args.break_after_first_file,
         args.rows_flush_interval,
         args.progress_msg_template,
         args.max_rows_per_file,
         char_xform_tuples_list)
    
    print(os.linesep + 'Processing finished!')

