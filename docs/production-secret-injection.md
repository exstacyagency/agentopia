# Production Secret Injection

This document defines the minimum production secret injection approach for Agentopia in its current scaffold state.

## Goals

- keep production secrets out of tracked repo files
- make secret loading explicit and repeatable
- separate template config from real secret material
- ensure operators know which secrets must be injected before rollout

## Secret injection policy

Production should not rely on committed `.env` values for real secrets.

Instead:

- keep tracked templates in `config/environments/`
- provide real secret values through an untracked production env file or secret manager export step
- inject secrets immediately before runtime validation and startup

## Minimum required production secrets

At minimum, production secret injection must provide:

- `PAPERCLIP_API_KEY`
- `HERMES_API_KEY`

Depending on the final runtime shape, additional secret values may be required later.

## Recommended current approach

For the current scaffold, use an untracked file such as:

```text
config/environments/production.secrets.env
```

This file should not be committed.

Then generate a merged runtime env file for deployment.

## Suggested flow

1. Start from the tracked production template:
   - `config/environments/production.env`
2. Create or update an untracked secrets file:
   - `config/environments/production.secrets.env`
3. Merge the template and secret values into a deployable env file
4. Validate the merged env file
5. Deploy using the merged env file as the runtime source

## Required operator checks

Before rollout:

- confirm the secrets file exists outside git-tracked config
- confirm the merged env file passes validation
- confirm the merged env file is not committed
- confirm production image refs are still digest-pinned

## Anti-patterns

Do not:

- commit real production secrets to `.env`, `.env.example`, or tracked templates
- reuse development or staging secret values in production
- skip validation after merging secret values

## Definition of done for this item

This repo can consider production secret injection minimally defined when:

- the secret injection path is documented
- an untracked secret file path is defined
- a merge step exists for template plus secrets
- validation of the merged result is part of the process
