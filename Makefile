test:
	python test_simpleeval.py

autotest:
	find . -name \*.py -not -path .\/.v\* | entr make test

.PHONY: test

dist/:
	python setup.py build sdist

pypi: test dist/
	twine upload dist/*

clean:
	rm -rf build
	rm -rf dist
	rm file.txt
