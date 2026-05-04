# Runbook

## Start Local Stack

```bash
make install
make up
make migrate
make seed
```

## Stop Local Stack

```bash
make down
```

## Migrations

```bash
make revision
make migrate
```

## Add A Node

1. Create the node in the admin API or UI and copy the one-time API key.
2. Store it in Ansible Vault as `gamehost_node_agent_api_key`.
3. Run `ansible-playbook -i inventory.ini deploy/ansible/node.yml --ask-vault-pass`.
4. Mark the node `online` in the admin UI.

## Roll Back

Deploy the previous image tag by setting `GAMEHOST_VERSION` and running:

```bash
docker compose -f deploy/docker-compose.prod.yml up -d
```

## Troubleshooting

- API health: `curl https://$GAMEHOST_DOMAIN/api/v1/healthz`
- Worker jobs: inspect `tasks` rows and worker logs.
- Node-agent: `systemctl status gamehost-node-agent`
- Backups: verify MinIO credentials and bucket access.
