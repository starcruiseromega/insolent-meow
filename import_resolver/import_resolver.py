# coding=utf-8
from __future__ import print_function, unicode_literals

__author__ = "Sally Wilsak"

import argparse
from collections import defaultdict
import os
import re
import sys


def extract_import_files(type_script_text):
	""" Find all the files imported in a block of TypeScript
	@param type_script_text: text to search
	@type type_script_text: str
	@return: a list of the filenames imported
	@rtype: list(str)
	"""
	import_re = r"""^import\s+\w+\s*=\s*require[(]['"](?P<fname>(?:[.]/|[.][.]/)\S+)['"][)]"""
	matches = re.findall(import_re, type_script_text, re.MULTILINE | re.UNICODE)
	# If the file doesn't end with ".ts", we should assume we should add it
	return [m if m.endswith(".ts") else m + ".ts" for m in matches]

def format_line(filename, dependents):
	""" Format an output line from a filename and its dependents
	@param filename: file that other files depend on
	@type filename: str
	@param dependents: list of the files that depend on filename
	@type dependents: list(str)
	@return: a single line suitable for output
	@rtype: str
	"""
	processed = [d.replace(" ", "\\ ") for d in dependents]
	return "%s <- %s" % (filename, " ".join(processed))


def read_file(filename):
	""" Opens a file and returns the contents. Factoring this out means we can override it in a test
	@param filename: name of file to read
	@type filename: str
	@return: contents of file
	@rtype: str
	"""
	with open(filename, "r") as fp:
		return fp.read()


def do_dependency_resolve(filenames):
	""" Resolves all the TypeScript-style imports in the specified files and returns a printable string with the reverse dependency graph
	@param filenames: list of absolute filenames to process
	@type filenames: list(str)
	@return: text representation of reverse dependency graph
	@rtype: str
	"""
	backward_deps = defaultdict(list)
	# Copy the filenames into another list so we don't destroy the params
	file_process_queue = list(filenames)
	files_processed = set()
	unreadable_files = list()
	while len(file_process_queue) > 0:
		# Pop off the front so that our list acts as a FIFO queue and we have a breadth-first search
		filename = file_process_queue.pop(0)
		if filename in files_processed:
			# We've already computed dependencies for this file, so don't bother doing it again
			continue
		files_processed.add(filename)
		try:
			text = read_file(filename)
		except IOError:
			unreadable_files.append(filename)
			continue
		file_dir = os.path.dirname(filename)
		dependees = [os.path.normpath(os.path.join(file_dir, p)) for p in extract_import_files(text)]
		for dependee in dependees:
			backward_deps[dependee].append(filename)
			file_process_queue.append(dependee)
		backward_deps[filename]
	output = [format_line(k, v) for k, v in backward_deps.items()]
	for unreadable_file in unreadable_files:
		output.append("Cannot read file '%s'" % unreadable_file)
	return "\n".join(output)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Prints out dependency graph of TypeScript file imports")
	parser.add_argument("filenames", metavar="FILENAMES", nargs="+", help="Paths of files to resolve")
	arguments = parser.parse_args(sys.argv[1:])
	abs_files = [os.path.abspath(f) for f in arguments.filenames]
	output = do_dependency_resolve(abs_files)
	print(output)
