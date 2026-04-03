.PHONY: setup validate doctor smoke contract-demo test-contract demo boot sample-task sample-task-budget template-check

setup:
	./scripts/setup.sh

validate:
	./scripts/validate.sh

doctor:
	./scripts/doctor.sh

smoke:
	./scripts/smoke.sh

sample-task:
	./scripts/sample-task.sh repo-summary

sample-task-budget:
	./scripts/sample-task.sh budget-check

template-check:
	python3 scripts/template-selector.py repo-summary
	python3 scripts/template-selector.py budget-check
	! python3 scripts/template-selector.py unknown-template

contract-demo:
	./scripts/contract-demo.sh

test-contract:
	python3 -c "import runpy; from pathlib import Path; ns = runpy.run_path('scripts/contract_runner.py'); runner = ns['ContractRunner'](Path('.')); request = {'task': {'id': 'task-123', 'title': 'Summarize repo changes', 'priority': 'medium', 'requester': {'id': 'human', 'displayName': 'human'}, 'budget': {'maxCostUsd': 5, 'maxRuntimeMinutes': 15}, 'approval': {'required': False}, 'constraints': {'outputFormat': 'markdown', 'outputLength': 'short', 'allowNetwork': False}, 'routing': {'inbound': 'paperclip', 'outbound': 'hermes'}}}; assert runner.validate_request(request)['id'] == 'task-123'; print('test-contract ok')"

demo: setup validate doctor smoke sample-task contract-demo test-contract template-check

boot: demo
