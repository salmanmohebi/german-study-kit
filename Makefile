.PHONY: install a1 a2 b1 b2 verbs themen a1-review a2-review review all clean

PY := .venv/bin/python

install:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

a1:
	$(PY) anki/build.py --level A1

a2:
	$(PY) anki/build.py --level A2

b1:
	$(PY) anki/build.py --level B1

b2:
	$(PY) anki/build.py --level B2

verbs:
	$(PY) anki/build_verbs.py

themen:
	$(PY) anki/build_themen.py

a1-review:
	$(PY) anki/build_review.py --level A1

a2-review:
	$(PY) anki/build_review.py --level A2

review: a1-review a2-review

all: a1 a2 b1 b2 verbs themen review

clean:
	rm -rf anki/out
