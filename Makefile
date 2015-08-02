test:
	django-admin.py test --settings tests.test_settings --pythonpath .
assets:
	cd leaflet_storage/static/storage/ && git pull && make install && make vendors
distfile:
	python setup.py sdist bdist_wheel
test_publish:
	twine upload -r testpypi dist/*
publish:
	twine upload dist/*
	make clean
clean:
	rm -f dist/*
	rm -rf build/*
tx_pull:
	tx pull
tx_pull:
	tx push -s
compilemessages:
	cd leaflet_storage && django-admin.py compilemessage
makemessages:
	cd leaflet_storage && django-admin.py makemessages -a
