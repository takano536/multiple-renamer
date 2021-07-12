import argparse
import glob
import os
import sys
import itertools
import functools
import re
import datetime
import collections
import random
import string


class ParserHelpOnError(argparse.ArgumentParser):
    def error(self, message):
        self.print_help()
        sys.stderr.write('\nerror: %s\n' % message)
        sys.exit(2)


parser = ParserHelpOnError(formatter_class=argparse.RawTextHelpFormatter)
parser.add_argument(
    '-i', '--input',
    required=True,
    nargs='*',
    help='input file or directory'
)
parser.add_argument(
    '-o', '--output_name',
    required=True,
    help='output filename pattern (example: "-o %%filename%% (#).%%ext%%") \n'
    '#                   : number with zero padding \n'
    '?                   : random character \n'
    '%%#%%                 : # (escape sequence) \n'
    '%%%%                  : %% (escape sequence) \n'
    '%%filename-with-ext%% : filename with extention \n'
    '%%filename%%          : filename without extention \n'
    '%%ext%%               : file extention \n'
    '%%foldername%%        : parent foldername \n'
    '%%creation-date%%     : creation date \n'
    '%%creation-time%%     : creation time \n'
    '%%modified-date%%     : modified date \n'
    '%%modified-time%%     : modified time \n'
    '%%size%%              : file size \n'
)
parser.add_argument(
    '-e', '--exclude',
    nargs='*',
    help='exclude file, directory or extension \n'
    'selecting an extension, prefix it with dot at the beginning'
)
parser.add_argument(
    '-r', '--replace',
    help='character replacement (example: "-r a:A")'
)
parser.add_argument(
    '-s', '--start_number',
    type=int,
    default='1',
    help='starting head number (default=1)'
)
parser.add_argument(
    '--used_char',
    choices=['upper', 'lower', 'number'],
    nargs='*',
    help='characters used in random characters'
)
parser.add_argument(
    '--sort',
    choices=['folder', 'file', 'date', 'ext', 'file-desc', 'folder-desc', 'date-desc', 'ext-desc'],
    default='folder',
    help='how to sort files (default=folder)'
)
parser.add_argument(
    '--recursive',
    action='store_true',
    help='recursively get input files'
)
parser.add_argument(
    '--sequence',
    action='store_true',
    help='sequential numbering across folders'
)
args = parser.parse_args()
if args.replace is not None and (args.replace[0] == ':' or args.replace.count(':') != 1):
    parser.error('invalid format: -r/--replace (ex: "-r a:A")')
if args.exclude is None:
    args.exclude = []


FULL_WIDTH = ''.join(chr(0xff01 + i) for i in range(94))
HALF_WIDTH = ''.join(chr(0x21 + i) for i in range(94))
FULL2HALF = str.maketrans(FULL_WIDTH, HALF_WIDTH)
SYMBOL_REGEX = '[\\u3000 !"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~]'
INVALID_CHAR_REGEX = '[\\/:*?"<>|]'
if args.used_char is None:
    RAND_STR = string.ascii_letters + string.digits
elif 'upper' in args.used_char and 'lower' in args.used_char:
    RAND_STR = string.ascii_letters
elif 'upper' in args.used_char and 'number' in args.used_char:
    RAND_STR = string.ascii_uppercase + string.digits
elif 'lower' in args.used_char and 'number' in args.used_char:
    RAND_STR = string.ascii_lowercase + string.digits
elif 'upper' in args.used_char:
    RAND_STR = string.ascii_uppercase
elif 'lower' in args.used_char:
    RAND_STR = string.ascii_lowercase
else:
    RAND_STR = string.digits


def natural_sort_cmp(a_str: str, b_str: str, ext_cmp: bool):
    def divide(string: str):
        substr = list()
        string = string.translate(FULL2HALF)
        string = [s.replace(os.sep, '/') for s in string]
        groups = itertools.groupby(string, lambda char: 1 if char.isdigit() else -1 if re.match(SYMBOL_REGEX, char) else 0)
        for _, group in groups:
            substr.append(''.join(group))
        return substr

    if ext_cmp and os.path.splitext(a_str)[1] != os.path.splitext(b_str)[1]:
        return 1 if os.path.splitext(a_str)[1] > os.path.splitext(b_str)[1] else -1

    a_dir_str, b_dir_str = divide(os.path.split(a_str)[0]), divide(os.path.split(b_str)[0])
    if len(a_dir_str) != len(b_dir_str):
        return 1 if len(a_str) > len(b_str) else -1

    a_str, b_str = divide(a_str), divide(b_str)
    rep_cnt = 0
    for (a_substr, b_substr) in zip(a_str, b_str):
        a_swap, b_swap = False, False
        if re.match(SYMBOL_REGEX, a_substr) and a_str[rep_cnt + 1].isdigit():
            a_str[rep_cnt], a_str[rep_cnt + 1] = a_str[rep_cnt + 1], a_str[rep_cnt]
            a_substr = a_str[rep_cnt]
            a_swap = True
        if re.match(SYMBOL_REGEX, b_substr) and b_str[rep_cnt + 1].isdigit():
            b_str[rep_cnt], b_str[rep_cnt + 1] = b_str[rep_cnt + 1], b_str[rep_cnt]
            b_substr = b_str[rep_cnt]
            b_swap = True

        if a_substr.isdigit() and b_substr.isdigit():
            a_substr = float(a_substr) - len(a_substr) * 0.1
            b_substr = float(b_substr) - len(b_substr) * 0.1

        if a_substr != b_substr:
            return 1 if a_substr > b_substr else -1

        if a_swap != b_swap:
            return 1 if b_swap else -1

        rep_cnt += 1

    if len(a_str) == len(b_str):
        return 0
    else:
        return 1 if len(a_str) > len(b_str) else -1


def input_filepaths(inputs: list, exc: list, is_recursive: bool):
    exc_ext, exc_file, exc_folder = list(), list(), list()
    for arg in exc:
        arg = arg.replace('/', os.sep)
        if arg[0] == '.':
            exc_ext.append(arg.lower())
        elif os.path.isfile(arg):
            exc_file.append(os.path.abspath(arg))
        elif os.path.isdir(arg):
            exc_folder.append(os.path.abspath(arg))

    filepaths = list()
    folders = list()
    for arg in inputs:
        arg = arg.replace('/', os.sep)
        arg = os.path.abspath(arg)
        if not os.path.exists(arg):
            continue
        if os.path.splitext(arg)[1].lower() in exc_ext:
            continue
        if arg in exc_file or arg in exc_folder:
            continue
        elif os.path.isfile(arg):
            filepaths.append(arg)
        elif os.path.isdir(arg):
            folders.append(arg)

    for folder in folders:
        for arg in glob.glob(folder + '/**/*.*' if is_recursive else folder + '/*.*', recursive=is_recursive):
            arg = arg.replace('/', os.sep)
            if not os.path.exists(arg):
                continue
            if not os.path.exists(arg):
                continue
            if os.path.splitext(arg)[1].lower() in exc_ext:
                continue
            if arg in exc_file:
                continue
            if os.path.split(arg)[0] in exc_folder:
                continue
            elif os.path.isfile(arg):
                filepaths.append(arg)

    for i in range(len(filepaths)):
        filepaths[i] = os.path.abspath(filepaths[i])
    return filepaths


def sort_files(filepaths: list, method: str):
    def filename_sort(a, b):
        return natural_sort_cmp(os.path.basename(a), os.path.basename(b), False)

    def foldername_sort(a, b):
        return natural_sort_cmp(a, b, False)

    def ext_sort(a, b):
        return natural_sort_cmp(a, b, True)

    if method == 'folder-desc':
        filepaths.sort(key=functools.cmp_to_key(foldername_sort), reverse=True)
    elif method == 'file':
        filepaths.sort(key=functools.cmp_to_key(filename_sort))
    elif method == 'file-desc':
        filepaths.sort(key=functools.cmp_to_key(filename_sort), reverse=True)
    elif method == 'date' and os.name == 'nt':
        filepaths.sort(key=lambda file_path: os.path.getctime(file_path))
    elif method == 'date-desc' and os.name == 'nt':
        filepaths.sort(key=lambda file_path: os.path.getctime(file_path), reverse=True)
    elif method == 'ext':
        filepaths.sort(key=functools.cmp_to_key(ext_sort))
    elif method == 'ext-desc':
        filepaths.sort(key=functools.cmp_to_key(ext_sort), reverse=True)
    else:
        filepaths.sort(key=functools.cmp_to_key(foldername_sort))
    return filepaths


def duplicate_rename(filepath: str):
    if not os.path.exists(filepath):
        return filepath

    file_cnt = 1
    while 1:
        filepath_without_ext, file_ext = os.path.splitext(filepath)
        filepath_without_ext += ' (' + str(file_cnt) + ')'
        if not os.path.exists(filepath_without_ext + file_ext):
            break
        file_cnt += 1
    return filepath_without_ext + file_ext


def get_rename_filepaths(filepaths: list):
    def divide(string: str):
        match = re.findall(r'%.*?%|#+|\?+', string)
        not_match = re.split(r'%.*?%|#+|\?+', string)
        substrs = list()
        for (char1, char2) in itertools.zip_longest(not_match, match):
            if not char1 == '' and char1 is not None:
                substrs.append(char1)
            if not char2 == '' and char2 is not None:
                substrs.append(char2)
        return substrs

    def calc_file_size(size: int):
        byte = 1024
        mbyte = pow(byte, 2)
        gbyte = pow(byte, 3)
        if size >= gbyte:
            div_num = gbyte
            unit = 'GB'
        elif size >= mbyte:
            div_num = mbyte
            unit = 'MB'
        else:
            div_num = byte
            unit = 'KB'
        filesize = '{:,}'.format(round(size / div_num, 2))
        return str(filesize) + unit

    def get_rand_str(n):
        return ''.join(random.choices(RAND_STR, k=n))

    sort_files(filepaths, args.sort)
    filenames = [os.path.split(filepath)[-1] for filepath in filepaths]
    dirpaths = [os.path.split(filepath)[0] for filepath in filepaths]
    pattern = divide(args.output_name)

    filepath_set = set()
    for dirpath in set(dirpaths):
        filepath_set = filepath_set.union(set(input_filepaths([dirpath], list(), is_recursive=False)))
    rename_filepath_set = filepath_set - set(filepaths)
    duplicate_filepath_cnt = collections.defaultdict(lambda: 0)

    rename_filenames = list()
    file_cnt = args.start_number
    file_count_each_folder = collections.defaultdict(lambda: args.start_number)
    for filepath, filename, dirpath in zip(filepaths, filenames, dirpaths):
        cnt = file_cnt if args.sequence else file_count_each_folder[dirpath]
        rename_filename = str()
        filename_without_ext = os.path.splitext(filename)[0]
        file_ext = os.path.splitext(filename)[1][1:]
        dirname = dirpath.split(os.sep)[-1]
        is_windows = bool(os.name == 'nt')
        if is_windows:
            creation_timestamp = datetime.datetime.fromtimestamp(os.path.getctime(filepath))
            creation_date = str(creation_timestamp).split()[0]
            creation_time = str(creation_timestamp).split()[1].split('.')[0].replace(':', '_')
        modified_timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
        modified_date = str(modified_timestamp).split()[0]
        modified_time = str(modified_timestamp).split()[1].split('.')[0].replace(':', '_')
        file_size = calc_file_size(os.path.getsize(filepath))

        for pattern_substr in pattern:
            if pattern_substr == r'%#%':
                rename_filename += '#'
            elif pattern_substr == r'%%':
                rename_filename += '%'
            elif pattern_substr == r'%filename-with-ext%':
                rename_filename += filename
            elif pattern_substr == r'%filename%':
                rename_filename += filename_without_ext
            elif pattern_substr == r'%ext%':
                rename_filename += file_ext
            elif pattern_substr == r'%foldername%':
                rename_filename += dirname
            elif pattern_substr == r'%creation-date%' and is_windows:
                rename_filename += creation_date
            elif pattern_substr == r'%creation-time%' and is_windows:
                rename_filename += creation_time
            elif pattern_substr == r'%modified-date%':
                rename_filename += modified_date
            elif pattern_substr == r'%modified-time%':
                rename_filename += modified_time
            elif pattern_substr == r'%size%':
                rename_filename += file_size
            elif '#' in pattern_substr:
                rename_filename += str(cnt).zfill(len(pattern_substr))
            elif '?' in pattern_substr:
                rename_filename += get_rand_str(len(pattern_substr))
            else:
                rename_filename += pattern_substr
        if args.replace is not None:
            original_char, replace_char = args.replace.split(':')
            rename_filename_witout_ext, rename_file_ext = os.path.splitext(rename_filename)
            rename_filename_witout_ext = rename_filename_witout_ext.replace(original_char, replace_char)
            rename_filename = rename_filename_witout_ext + rename_file_ext

        rename_filepath = os.path.join(dirpath, rename_filename)
        while {rename_filepath}.issubset(rename_filepath_set):
            duplicate_filepath_cnt[rename_filepath] += 1
            filepath_without_ext, file_ext = os.path.splitext(rename_filepath)
            filepath_without_ext += ' (' + str(duplicate_filepath_cnt[rename_filepath]) + ')'
            rename_filepath = filepath_without_ext + file_ext
        rename_filenames.append(rename_filepath)
        rename_filepath_set.add(rename_filepath)
        file_cnt += 1
        file_count_each_folder[dirpath] += 1

    return rename_filenames


def preview(filepaths, rename_filepaths):
    filenames = [os.path.split(filepath)[-1] for filepath in filepaths]
    rename_filenames = [os.path.split(filepath)[-1] for filepath in rename_filepaths]
    pre_dirpath = str()
    for filename, rename_filename, filepath in zip(filenames, rename_filenames, filepaths):
        dirpath = os.path.split(filepath)[0]
        if not dirpath == pre_dirpath:
            print('\n' + dirpath)
        pre_dirpath = dirpath

        if re.search(INVALID_CHAR_REGEX, rename_filename):
            print(filename, '->', rename_filename, '   Warning: Contains invalid characters')
        else:
            print(filename, '->', rename_filename)
    return


def rename(filepaths, rename_filepaths):
    temp_filepaths = list()
    for filepath, rename_filepath in zip(filepaths, rename_filepaths):
        rename_filename = os.path.split(rename_filepath)[-1]
        if re.search(INVALID_CHAR_REGEX, rename_filename):
            return -1

        duplicate_rename_filepath = duplicate_rename(rename_filepath)
        try:
            os.rename(filepath, duplicate_rename_filepath)
        except Exception:
            print('Unexpected error occurred.')
            return -1
        else:
            temp_filepaths.append(duplicate_rename_filepath)

    is_failed = False
    undo_filepaths = list()
    for filepath, temp_filepath, rename_filepath in zip(filepaths, temp_filepaths, rename_filepaths):
        try:
            os.rename(temp_filepath, rename_filepath)
        except Exception:
            undo_filepaths.append([filepath, temp_filepath, None])
            is_failed = True
        else:
            undo_filepaths.append([filepath, temp_filepath, rename_filepath])

    if not is_failed:
        return 0

    for _, temp_filepath, rename_filepath in reversed(undo_filepaths):
        if rename_filepath is None:
            continue
        try:
            os.rename(rename_filepath, temp_filepath)
        except Exception:
            continue
    for filepath, temp_filepath, _ in reversed(undo_filepaths):
        try:
            os.rename(temp_filepath, filepath)
        except Exception:
            continue
    return -1


def main():
    filepaths = input_filepaths(args.input, args.exclude, args.recursive)
    sorted_filepaths = sort_files(filepaths, args.sort)

    rename_filepaths = get_rename_filepaths(sorted_filepaths)
    preview(sorted_filepaths, rename_filepaths)
    print('\nProceed ([y]/n)? ', end='')
    ans = input()
    should_rename = True if len(ans) != 0 and ans[0].lower() == 'y' else False
    if not should_rename:
        return

    ret = rename(sorted_filepaths, rename_filepaths)
    if ret == 0:
        print('\nRename was successful.')
    else:
        print('\nRename failed.')


if __name__ == '__main__':
    main()
    sys.exit(0)
