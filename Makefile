test:
	python test_simpleeval.py

autotest:
	find . -name \*.py -not -path .\/.v\* | entr make test

.PHONY: test

dist/: setup.py simpleeval.py README.rst
	python setup.py build sdist
	twine check dist/*

pypi: test dist/
	twine check dist/*
	twine upload dist/*

clean:
	rm -rf build
	rm -rf dist
	rm file.txt
