# coding=utf-8
from __future__ import print_function, unicode_literals

__author__ = "Sally Wilsak"

import codecs
import os
import sys
import textwrap
import unittest

import import_resolver

# This isn't strictly correct; it will only work properly if your terminal is set to UTF-8.
# However, Linux is usually set to UTF-8 and Windows' English code page 437 is at least ASCII-compatible this will work well enough for our purposes
if sys.stdout.encoding != 'utf8':
  sys.stdout = codecs.getwriter('utf8')(sys.stdout, 'strict')
if sys.stderr.encoding != 'utf8':
  sys.stderr = codecs.getwriter('utf8')(sys.stderr, 'strict')


def simple_normpath(path):
	"""On Windows, normpath substitutes back slashes into the file path.
	This makes cross-platform testing difficult since we're checking string output.
	But the test cases have simple filepaths so we can substitute something simpler for the tests.
	"""
	return path.replace("./", "")

def simple_join(path, *args):
	""" Make os.path.join work the same on Windows and Linux. Again this is ok because the test cases have simple paths
	"""
	elements = [path]
	elements.extend(args)
	return "/".join(elements)

class TestImportResolver(unittest.TestCase):
	def setUp(self):
		# Monkey-patch some path manipulations so we can string match with Unix-style paths and Windows won't mess them up
		import_resolver.os.path.normpath = simple_normpath
		import_resolver.os.path.join = simple_join

	def test_line_extraction(self):
		self.assertEqual(import_resolver.extract_import_files(""), [])
		self.assertEqual(import_resolver.extract_import_files("This isn't TypeScript.\nBut it does have multiple lines."), [])
		self.assertEqual(import_resolver.extract_import_files("import thing = require('./thing.ts');"), ["./thing.ts"])
		import_statements = textwrap.dedent("""
		// Comments should get ignored, of course
		import first = require('./lib/first.ts');
		// Different amounts of whitespace should be ok
		import  second=require('./second.ts')  ; // so should other stuff at the end
		// Double quotes are also ok
		import _THIRD = require("./third.ts")
		// So is something that's not a ts file, but it gets .ts added
		import fourth = require("../fourth/file/path")
		// A Windows-style path doesn't match...
		import fifth = require("C:\\fifth.ts")
		// ...neither does an absolute Unix-style path...
		import sixth = require("/home/user6/sixth.ts")
		// ...but this mixed-up one does
		import seventh = require('./folder\\folder\\seventh.ts')
		// Capitalizing the keywords means it doesn't match
		Import eighth = Require('./eighth.ts')
		// Something that's not a file path doesn't match
		import ninth = require('ninth')
		// If it's not at the start of the line, it doesn't match
		some stuff import tenth = require('./tenth.ts')
		// And for good measure, a non-ASCII file path should work
		import eleventh = require('./одиннадцать.ts')
		""")
		expected_filenames = [
			"./lib/first.ts",
			"./second.ts",
			"./third.ts",
			"../fourth/file/path.ts",
			"./folder\\folder\\seventh.ts",
			"./одиннадцать.ts",
		]
		self.assertEqual(import_resolver.extract_import_files(import_statements), expected_filenames)
		
	def test_format(self):
		files = ["/badger/badger", "C:\\badger.ts", "/bad ger/snake.ts"]
		self.assertEqual(import_resolver.format_line("/file/name.ts", files), "/file/name.ts <- /badger/badger C:\\badger.ts /bad\\ ger/snake.ts")

	def test_circular_deps(self):
		circular_deps = {
			"/home/badger/a.ts": "import b = require('./b.ts');\nimport c = require('./c.ts');",
			"/home/badger/b.ts": "import d = require('./d.ts');",
			"/home/badger/c.ts": "",
			"/home/badger/d.ts": "import a = require('./a.ts');",
		}
		import_resolver.read_file = lambda x: circular_deps[x]
		expected_string = "\n".join([
		   	"/home/badger/c.ts <- /home/badger/a.ts",
		   	"/home/badger/d.ts <- /home/badger/b.ts",
		   	"/home/badger/a.ts <- /home/badger/d.ts",
			"/home/badger/b.ts <- /home/badger/a.ts",
		])
		self.assertEqual(import_resolver.do_dependency_resolve(["/home/badger/a.ts"]), expected_string)

	def test_triangle_deps(self):
		triangle_deps = {
			"/home/badger/a.ts": "import b = require('./b.ts');\nimport c = require('./c.ts');",
			"/home/badger/b.ts": "import c = require('./c.ts');",
			"/home/badger/c.ts": "",
		}
		import_resolver.read_file = lambda x: triangle_deps[x]
		expected_string = "\n".join([
			"/home/badger/c.ts <- /home/badger/a.ts /home/badger/b.ts",
			"/home/badger/a.ts <- ",
			"/home/badger/b.ts <- /home/badger/a.ts",
		])
		self.assertEqual(import_resolver.do_dependency_resolve(["/home/badger/a.ts"]), expected_string)

	def test_inaccessible_deps(self):
		def inaccessible_deps(filename):
			if "a.ts" in filename:
				return "import b = require('./b.ts');"
			elif "b.ts" in filename:
				return "import c = require('./c.ts');"
			raise IOError
		import_resolver.read_file = inaccessible_deps
		expected_string = "\n".join([
			"/home/badger/c.ts <- /home/badger/b.ts",
			"/home/badger/a.ts <- ",
			"/home/badger/b.ts <- /home/badger/a.ts",
			"Cannot read file '/home/badger/c.ts'",
		])
		self.assertEqual(import_resolver.do_dependency_resolve(["/home/badger/a.ts"]), expected_string)

	def test_lists(self):
		lists_deps = {
			"/home/badger/a.ts": "import b = require('./b.ts');\nimport c = require('./c.ts');\nimport d = require('./d.ts');",
			"/home/badger/b.ts": "import c = require('./c.ts');\nimport d = require('./d.ts');",
			"/home/badger/c.ts": "import d = require('./d.ts');",
			"/home/badger/d.ts": "",
		}
		import_resolver.read_file = lambda x: lists_deps[x]
		expected_string = "\n".join([
		   	"/home/badger/c.ts <- /home/badger/a.ts /home/badger/b.ts",
		   	"/home/badger/d.ts <- /home/badger/a.ts /home/badger/b.ts /home/badger/c.ts",
			"/home/badger/a.ts <- ",
			"/home/badger/b.ts <- /home/badger/a.ts",
		])
		self.assertEqual(import_resolver.do_dependency_resolve(["/home/badger/a.ts"]), expected_string)


