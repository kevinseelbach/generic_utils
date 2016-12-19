"""
Various file utilities
"""
# stdlib
import os
import re


def which(program, paths=None):
    """
    Returns the full path of the program requested if it exists within the PATH environment variable.
    :param program:
    :return:
    """
    import os

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        if paths is None:
            paths = [path.strip('"') for path in os.environ["PATH"].split(os.pathsep)]

        for path in paths:
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def get_file_list(root_dir,
                  include_exts=None,
                  exclude_exts=None,
                  exclude_private_dirs=True,
                  excluded_dir_patterns=None):
    """
    Returns a list of files within a root directory that match the provided criteria.

    Arguments:
    root_dir -- The root directory to search
    include_exts -- An iterable of the file_name extensions to include in the results.  If not provided, then all are
                    included unless explicitly excluded
    exclude_exts -- An iterable of the file_name extensions to explicitly exclude from the results.
    exclude_private_dirs -- Whether or not to exclude private directories in the search
    excluded_dir_patterns -- Iterable of patterns for sub directories to exclude from the search
    """
    return_list = []
    for root, dirs, files in os.walk(root_dir):
        if exclude_private_dirs:
            #Uuuuuuuugly, but safe
            dirs_to_remove = []
            for current_dir in dirs:
                if current_dir.startswith("."):
                    dirs_to_remove.append(current_dir)
            for current_dir in dirs_to_remove:
                dirs.remove(current_dir)
                # Remove private dirs from contention
                #dirs = [current_dir for current_dir in dirs if not current_dir.startswith(".")]

        if excluded_dir_patterns:
            dirs_to_remove = []
            for current_dir in dirs:
                full_path = os.path.join(root, current_dir)
                for pattern in excluded_dir_patterns:
                    if re.search(pattern, full_path):
                        dirs_to_remove.append(current_dir)
                        break

            for current_dir in dirs_to_remove:
                dirs.remove(current_dir)

        for file_name in files:
            include = True
            relpath = os.path.join(root[len(root_dir) + 1:], file_name)
            if include_exts: # Do explicit includes
                include = False
                for ext in include_exts:
                    if file_name.endswith("." + ext):
                        include = True
                        break

            if exclude_exts:
                for ext in exclude_exts:
                    if file_name.endswith("." + ext):
                        include = False
                        break

            if include:
                return_list.append(relpath)

    return return_list
