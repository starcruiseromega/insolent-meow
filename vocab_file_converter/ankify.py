# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import argparse
import codecs
import sys

parser = argparse.ArgumentParser("Changes SuperMemo Q/A files into Anki comma-separated files")
parser.add_argument("--infile", help="Input SuperMemo format file")
parser.add_argument("--outfile", help="Output file to append Anki-style notes",
		    default="anki_vocab.txt")

if __name__ == '__main__':
	args = parser.parse_args(sys.argv[1:])
	with codecs.open(args.infile, "r", "utf-8") as f_in:
		with codecs.open(args.outfile, "a", "utf-8") as f_out:
			lines = [li for li in f_in.readlines() if not li.isspace()]
			while lines:
				question = lines.pop(0)
				answer = lines.pop(0)
				f_out.write('"')
				f_out.write(question.replace("Q: ", "").rstrip())
				f_out.write('"')
				f_out.write(";")
				f_out.write('"')
				f_out.write(answer.replace("A: ", "").rstrip())
				f_out.write('"')
				f_out.write("\r\n")
