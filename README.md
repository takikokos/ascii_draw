This is my ASCI DRAW project

I know that there is better way to do it(google non-negative matrix factorization), but i decided to go my own way.
I think i got very similar result using the basic idea:
- devide image into small rectangles with same aspect ratio as letter
- for each rectangle choose letter which fits the best to image in this rectangle (i compared covered area ratio of symbol and greyscaled image)

More explanations in source code :)

Usage:

~$ python3 -m vevn env

~$ source ./env/bin/activate

~$ pip install -r requirements.txt

~$ python ascdraw.py -h

 
P.S. there are some images i tested my methods on and results i got in folders 
