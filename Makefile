test:
	python test_simpleeval.py
.PHONY: test

dist/:
	python setup.py build sdist

pypi: test dist/
	twine upload dist/*

clean:
	rm -rf build
	rm -rf dist
	rm file.txt
