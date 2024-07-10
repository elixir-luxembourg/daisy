# Ansible scripts for Daisy deployment and management

Supported distributions: **Rocky Linux 8**

## Provisioning

1. Rename `inventory_template.yaml` to `inventory.yaml` and populate it with your guest machine information
2. Run following:

    ```bash
     ansible-playbook -i inventory.yaml install_daisy.yaml
    ```

3. Create/update your settings in `settings_local.py` - Haystack and postgresql connections
4. Restart `gunicorn`:

   ```bash
   systemctl restart gunicorn
   ```

## Updating DAISY
Following playbook does not contain backup generation so be sure the environment is properly backed up.

    ```bash
     ansible-playbook -i inventory.yaml update_daisy.yaml
    ```
