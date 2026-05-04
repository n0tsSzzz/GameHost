# Ansible

Run with:

```bash
ansible-playbook -i inventory.ini deploy/ansible/node.yml --ask-vault-pass
```

Required vaulted variables:

- `gamehost_node_agent_api_key`
- `gamehost_image_repository`
