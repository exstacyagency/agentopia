# Production Readiness Checklist

This checklist captures the minimum work required before Agentopia should be used by a paying client.

## P0: Must be done before any paying client

### Auth, tenants, and permissions
- [ ] Add client/org/tenant isolation
- [ ] Add authentication for all client-facing APIs
- [ ] Add role-based permissions
- [ ] Add scoped API keys
- [ ] Add API key rotation and revocation

### Execution sandbox and safety controls
- [ ] Add sandboxed execution for Hermes actions
- [ ] Add per-tool permission enforcement
- [ ] Add network egress controls
- [ ] Add strict write boundaries
- [ ] Add resource and time limits
- [ ] Add cancellation support
- [ ] Add a safer shell execution layer

### Durable job/runtime system
- [ ] Add a durable queue
- [ ] Add retries with backoff
- [ ] Add timeout enforcement
- [ ] Add worker claiming and leasing
- [ ] Add idempotent task submission
- [ ] Add idempotent result handling
- [ ] Add stuck-job recovery
- [ ] Add dead-letter handling

### Production persistence
- [ ] Move to Postgres or equivalent production database
- [ ] Add migrations
- [ ] Add transactional state updates where needed
- [ ] Add durable storage layout for artifacts and results
- [ ] Add backup and restore plan
- [ ] Add retention and deletion workflows

### Security and secrets
- [ ] Add secret storage and handling strategy
- [ ] Add stronger service-to-service authentication
- [ ] Add audit logging
- [ ] Add request size limits
- [ ] Add rate limiting and abuse protection
- [ ] Add safer input validation and sanitization
- [ ] Add dependency and vulnerability scanning
- [ ] Add image and dependency provenance checks
- [ ] Add artifact access controls and sensitive-output redaction rules

### Build, release, and supply chain hygiene
- [x] Add a proper Python project/dependency manifest
- [x] Add pinned dependency resolution or lockfile support
- [x] Add reproducible build/install steps for local, CI, and production
- [x] Add CI validation in a clean environment
- [x] Add container/image versioning strategy
- [x] Add release and promotion criteria for staging to production

### Observability and operations
- [ ] Add structured logging
- [ ] Add correlation IDs across requests and runs
- [ ] Add metrics
- [ ] Add alerts
- [ ] Add tracing or equivalent request/run visibility
- [ ] Add dependency-aware health checks
- [ ] Add operator runbooks for common failures

### Governance and approval correctness
- [ ] Add reliable approval state reconciliation
- [ ] Add approval expiration and timeout behavior
- [ ] Add audit trail for approval actions
- [ ] Add operator recovery tools for stuck approval states

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
- [ ] Add repeatable deployment process
- [ ] Add staging environment
- [ ] Add rollback process
- [ ] Add per-environment config validation
- [ ] Add production secret injection
- [ ] Harden runtime and container setup

### Test coverage for dangerous paths
- [ ] Add auth tests
- [ ] Add tenancy isolation tests
- [ ] Add dangerous action tests for file_write, repo_write, and shell_command
- [ ] Add retry and reconciliation tests
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
