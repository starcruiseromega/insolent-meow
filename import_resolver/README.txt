This script was put together for a code challenge.

I tested this with Python 2.7.6. It might also work with Python 3 because I usually try to be
Python 3 compatible but I didn't actually try it.

Run the script with:
$ python import_resolver.py file1.ts file2.ts...

Run the unittests with:
$ python -m unittests discover

I used Windows for my testing because that's what I have at home (although I usually prefer Linux
for developing Python), which is why there's some monkey patching in the unittests. I tried to call
out any assumptions made in the code or the tests.