# Ansible deployment

Playbooks for preparing the VM, building the backend Docker image, and updating
the production Docker Compose stack.

## Required variables

Set these variables in CI/CD variables or export them locally before deployment:

```bash
export DOCKER_IMAGE_NAME=studiom-backend
export DOCKER_IMAGE_TAG=latest
export DOCKER_USER=<dockerhub-user>
export DOCKER_TOKEN=<dockerhub-token>

export DB__USER=postgres
export DB__PASSWORD=<strong-password>
export DB__NAME=gsp
export AUTH__SECRET=<jwt-secret>
export RBAC__ADMIN_EMAIL=<admin-email>
export RBAC__ADMIN_PASSWORD=<admin-password>
export COMMON__HOST=<duckdns-domain>
```

Optional application variables can also be passed through environment variables
before running the compose update playbook.

## Commands

Run all commands from the `ansible` directory.

```bash
ansible-playbook playbooks/init-vm-playbook.yaml
ansible-playbook playbooks/build-image-playbook.yaml
ansible-playbook playbooks/compose-update-playbook/yaml
```

Or build, push, and deploy with one command:

```bash
ansible-playbook playbooks/deploy.yaml
```

Validate playbooks:

```bash
ansible-lint .
```

The production Compose stack includes Nginx Proxy Manager and exposes ports
`80`, `81`, and `443`. After deployment, configure the proxy host and
Let's Encrypt certificate through the Nginx Proxy Manager admin UI.
