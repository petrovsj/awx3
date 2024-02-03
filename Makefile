# Taken from: https://github.com/sensu/sensu-go-ansible/blob/master/Makefile

# Make sure we have ansible_collections/zscaler/zpacloud_enhanced
# as a prefix. This is ugly as heck, but it works. I suggest all future
# developer to treat next few lines as an opportunity to learn a thing or two
# about GNU make ;)
collection := $(notdir $(realpath $(CURDIR)      ))
namespace  := $(notdir $(realpath $(CURDIR)/..   ))
toplevel   := $(notdir $(realpath $(CURDIR)/../..))

err_msg := Place collection at <WHATEVER>/ansible_collections/zscaler/zpacloud
ifneq (zpacloud,$(collection))
  $(error $(err_msg))
else ifneq (zscaler,$(namespace))
  $(error $(err_msg))
else ifneq (ansible_collections,$(toplevel))
  $(error $(err_msg))
endif

python_version := $(shell \
  python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))' \
)


.PHONY: help
help:
	@echo Available targets:
	@fgrep "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sort

.PHONY: docs
docs:		## Build collection documentation
	sudo make install
	rm -rf antsibull
	mkdir antsibull
	poetry run antsibull-docs collection --use-current --dest-dir antsibull --no-indexes zscaler.zpacloud
	mkdir -p docs/source/modules
	mv antsibull/collections/zscaler/zpacloud/* docs/source/modules
	rm -rf antsibull
	rm -f docs/source/modules/index.rst
	cd docs && sphinx-build source html

.PHONY: clean
clean:		## Remove all auto-generated files
	rm -rf tests/output
	rm -rf *.tar.gz

.PHONY: format
format:		## Format with black
	black .

.PHONY: check-format
check-format:	## Check with black
	black --check --diff .

.PHONY: old-sanity
old-sanity:		## Sanity tests for Ansible v2.9 and Ansible v2.10
	ansible-test sanity -v --skip-test pylint --skip-test rstcheck --python $(python_version)

.PHONY: new-sanity
new-sanity:		## Sanity tests for Ansible v2.11 and above
	ansible-test sanity -v --skip-test pylint --python $(python_version)

.PHONY: reqs
reqs:       ## Recreate the requirements.txt file
	poetry export -f requirements.txt --output requirements.txt

install:
	cp -R /Users/wguilherme/ansible_collections/zscaler/zpacloud /opt/homebrew/lib/python3.11/site-packages/ansible_collections/zscaler/
	rm -f zscaler*
	ansible-galaxy collection build . --force
	ansible-galaxy collection install zscaler* --force
	rm -f zscaler*