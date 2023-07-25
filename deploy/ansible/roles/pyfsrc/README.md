pyfsrc: Python from source
==========================

Ansible role for installing a particular version of Python from
source.

Requirements
------------

None

Role Variables
--------------

The only role vars that the user needs to worry about are:

- `pyfsrc_version`: The version of python to install
- `pyfsrc_make_default`: Whether to make this version of python the
  default version on the system.
- `pyfsrc_force_install`: Install again even if the specified version
  is already found.
- `pyfsrc_extra_sys_pkgs`: Install additional system packages

Dependencies
------------

None

Example Playbook
----------------

eg:

```
    - name: Install python
      hosts: localhost
      sudo: yes
      roles:
        - role: pyfsrc
          pyfsrc_version: 3.8
```

The above playbook will install python version 3.8

The role can be used multiple times with different value of
`pyfsrc_version` to install different versions. This can be useful for
setting up an environment for testing a python lib against multiple
versions by using tox for eg.

License
-------

MIT

Author Information
------------------

Vineet Naik <naikvin@gmail.com>
