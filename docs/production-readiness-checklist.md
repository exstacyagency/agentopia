# Production Readiness Checklist

This checklist captures the minimum work required before Agentopia should be used by a paying client.

## P0: Must be done before any paying client

### Auth, tenants, and permissions
- [x] Add client/org/tenant isolation
- [x] Add authentication for all client-facing APIs
- [x] Add role-based permissions
- [x] Add scoped API keys
- [x] Add API key rotation and revocation

### Execution sandbox and safety controls
- [ ] Add sandboxed execution for Hermes actions
- [x] Add per-tool permission enforcement
- [ ] Add network egress controls
- [x] Add strict write boundaries
- [ ] Add resource and time limits
- [ ] Add cancellation support
- [ ] Add a safer shell execution layer

### Durable job/runtime system
- [x] Add a durable queue
- [x] Add retries with backoff
- [x] Add timeout enforcement
- [x] Add worker claiming and leasing
- [x] Add idempotent task submission
- [x] Add idempotent result handling
- [x] Add stuck-job recovery
- [x] Add dead-letter handling

### Production persistence
- [x] Move to Postgres or equivalent production database
- [x] Add migrations
- [x] Add transactional state updates where needed
- [x] Add durable storage layout for artifacts and results
- [x] Add backup and restore plan
- [x] Add retention and deletion workflows

### Security and secrets
- [x] Add secret storage and handling strategy
- [x] Add stronger service-to-service authentication
- [x] Add audit logging
- [x] Add request size limits
- [x] Add rate limiting and abuse protection
- [x] Add safer input validation and sanitization
- [x] Add dependency and vulnerability scanning
- [x] Add image and dependency provenance checks
- [x] Add artifact access controls and sensitive-output redaction rules

### Build, release, and supply chain hygiene
- [x] Add a proper Python project/dependency manifest
- [x] Add pinned dependency resolution or lockfile support
- [x] Add reproducible build/install steps for local, CI, and production
- [x] Add CI validation in a clean environment
- [x] Add container/image versioning strategy
- [x] Add release and promotion criteria for staging to production

### Observability and operations
- [x] Add structured logging
- [x] Add correlation IDs across requests and runs
- [x] Add metrics
- [x] Add alerts
- [x] Add tracing or equivalent request/run visibility
- [x] Add dependency-aware health checks
- [x] Add operator runbooks for common failures

### Governance and approval correctness
- [x] Add reliable approval state reconciliation
- [x] Add approval expiration and timeout behavior
- [x] Add audit trail for approval actions
- [x] Add operator recovery tools for stuck approval states

### Memory safety
- [ ] Add tenant-scoped memory boundaries
- [ ] Add memory deletion workflows
- [ ] Add fallback behavior when MemPalace is unavailable
- [ ] Clarify native memory vs MemPalace contracts
- [ ] Add memory provenance to execution and audit surfaces

### Client-usable product surface
- [ ] Publish a stable public API contract
- [ ] Add customer-usable API docs
- [ ] Add onboarding and setup instructions
- [ ] Add task status and history visibility
- [ ] Add approval and review visibility where relevant
- [ ] Add key management path
- [ ] Return sane, consistent error messages

### Deployment maturity
- [x] Add repeatable deployment process
- [x] Add staging environment
- [x] Add rollback process
- [x] Add per-environment config validation
- [x] Add production secret injection
- [x] Harden runtime and container setup

### Test coverage for dangerous paths
- [x] Add auth tests
- [x] Add tenancy isolation tests
- [ ] Add dangerous action tests for file_write, repo_write, and shell_command
- [x] Add retry and reconciliation tests
- [ ] Add end-to-end HTTP/process tests
- [ ] Add failure-path tests

## P1: Important soon after first paid usage
- [ ] Add OpenAPI spec
- [ ] Add webhook ergonomics and client helpers
- [ ] Add approval dashboard improvements
- [ ] Add richer governance reporting
- [ ] Add stronger memory quality evaluation
- [ ] Add broader performance and load testing

## Later
- [ ] Add SDKs
- [ ] Add billing and usage UI
- [ ] Add self-serve onboarding
- [ ] Add compliance packaging and trust artifacts
- [ ] Add deeper chaos and scale testing
