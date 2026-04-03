.PHONY: setup validate doctor smoke contract-demo test-contract demo boot sample-task sample-task-budget template-check task-run

setup:
	./scripts/agentopia setup

validate:
	./scripts/agentopia validate

doctor:
	./scripts/agentopia doctor

smoke:
	./scripts/agentopia smoke

sample-task:
	./scripts/agentopia sample-task

sample-task-budget:
	./scripts/agentopia sample-task-budget

template-check:
	./scripts/agentopia template-check

contract-demo:
	./scripts/agentopia contract-demo

task-run:
	./scripts/agentopia task-run

test-contract:
	./scripts/agentopia test-contract

demo: boot

boot:
	./scripts/agentopia boot
