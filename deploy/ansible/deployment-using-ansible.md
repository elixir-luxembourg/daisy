# Ansible scripts for Daisy deployment and management

1. Rename `inventory_template.yaml` to `inventory.yaml` and populate it with the connection information
2. Run following:
    ```bash
     ansible-playbook -i inventory.yaml update_daisy.yaml
    ```
