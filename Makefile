# Thin wrapper around run.py so that `make <target>` and `python run.py <target>`
# do the same thing (Windows users without make can use run.py directly).
PY ?= python
.PHONY: setup data tables eda sq1 sq2 sq3 report app test all
setup:
	$(PY) -m pip install -r requirements.txt
data tables eda sq1 sq2 sq3 report app test all:
	$(PY) run.py $@
