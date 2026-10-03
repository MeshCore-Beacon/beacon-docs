"""Refresh the declared Beacon PR stack without touching unrelated work."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import shutil
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'planning/review-stack.json'
STATE = ROOT / 'evidence/review-stack'
GENERATED = {'docs/docs.go', 'docs/swagger.json', 'docs/swagger.yaml'}
ENV = dict(os.environ, GOMAXPROCS='2', GOFLAGS='-p=2', GIT_EDITOR='true')
# Cached local checks are unit checks. Database verification uses the explicit
# private Pi/CI workflows, never an accidentally inherited connection target.
ENV.pop('BEACON_TEST_POSTGRES_DSN', None)
ENV['BEACON_BACKUP_TEST_POSTGRES'] = '0'
GUARD_SCRIPT = os.environ.get('BEACON_GUARD_SCRIPT')


def local_path(value):
    path = Path(value)
    return (path if path.is_absolute() else ROOT/path).resolve()


def check_remotes(repo, manifest):
    if any(not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', manifest[key]) for key in ('upstream', 'fork')):
        raise RuntimeError('Expected GitHub owner/repository names')
    def slug(remote):
        url = git(repo, 'remote', 'get-url', remote).stdout.strip().removesuffix('.git')
        for prefix in ('https://github.com/', 'git@github.com:'):
            if url.startswith(prefix):
                return url[len(prefix):].lower()
        return None
    if slug('origin') != manifest['upstream'].lower() or slug(manifest['remote']) != manifest['fork'].lower():
        raise RuntimeError('Repository remotes do not match the declared upstream and contribution fork')


def command(args, cwd=None, check=True, log=None):
    result = subprocess.run(args, cwd=cwd, env=ENV, text=True, encoding='utf-8',
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if log:
        Path(log).write_text(result.stdout, encoding='utf-8')
    if check and result.returncode:
        raise RuntimeError(f"{args[0]} {args[1]} failed in {cwd or ROOT}:\n{result.stdout}")
    return result


def git(repo, *args, check=True):
    return command(['git', *args], cwd=repo, check=check)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.new')
    temporary.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def active_entries(entries, pulls):
    active = []
    for entry, pull in zip(entries, pulls, strict=True):
        if pull['merged']:
            continue
        if pull['state'] != 'open':
            raise RuntimeError(f"PR #{entry['pr']} was closed without merging; resolve its disposition first")
        if pull['head']['sha'] != entry['remote_head'] or pull['head']['ref'] != entry['branch']:
            raise RuntimeError(f"PR #{entry['pr']} changed outside this stack; inspect before updating")
        if pull['base']['ref'] != 'dev':
            raise RuntimeError('Unexpected PR target; this workflow only targets dev')
        if any(not re.fullmatch(r'[a-f0-9]{40}', entry.get(key, '')) for key in ('base', 'head', 'remote_head')):
            raise RuntimeError('Stack boundaries must be exact commit IDs')
        if entry['branch'] in ('main', 'master', 'dev'):
            raise RuntimeError('Contribution branches must not be default or release branches')
        active.append(entry.copy())
    return active


def guard(path, mode, receipt):
    path = local_path(path)
    branch = git(path, 'branch', '--show-current').stdout.strip()
    if not branch or branch in ('main', 'master', 'dev') or git(path, 'status', '--porcelain').stdout:
        raise RuntimeError(f'Clean, isolated feature branch required: {path}')
    if GUARD_SCRIPT:
        if not Path(GUARD_SCRIPT).is_file():
            raise RuntimeError('Configured repository guard is missing; no changes are permitted')
        command(['pwsh', '-NoProfile', '-File', GUARD_SCRIPT, '-Mode', mode, '-RepoPath', str(path),
                 '-Base', 'origin/dev', '-NoRemote', '-OutputPath', str(receipt)], log=receipt.with_suffix('.log'))
        if not json.loads(receipt.read_text(encoding='utf-8-sig'))['ready']:
            raise RuntimeError('Repository guard did not pass')
    else:
        write(receipt, dict(ready=True, branch=branch, head=git(path, 'rev-parse', 'HEAD').stdout.strip(), clean=True))


def verify_publish_state(manifest, plan):
    # Validation can take minutes. Refresh these inputs immediately before the
    # leased push, including Sync mode, rather than trusting its initial snapshot.
    base = command(['gh', 'api', f"repos/{manifest['upstream']}/commits/dev", '--jq', '.sha']).stdout.strip()
    pulls = [json.loads(command(['gh', 'api', f"repos/{manifest['upstream']}/pulls/{e['pr']}"]).stdout) for e in manifest['entries']]
    if any(p['head']['repo']['full_name'] != manifest['fork'] for p in pulls):
        raise RuntimeError('The contribution fork changed during validation')
    active = active_entries(manifest['entries'], pulls)
    if plan['base'] != base or [e['pr'] for e in plan['entries']] != [e['pr'] for e in active]:
        raise RuntimeError('Upstream or merge state changed during validation; refresh again. Verified trees remain cached.')
    if plan.get('preview_overlays', []) != active_overlays(manifest):
        raise RuntimeError('Independent preview overlays changed during validation; refresh again. Verified trees remain cached.')


def rebase(path, parent, previous_base, kind='server'):
    result = git(path, 'rebase', '--onto', parent, previous_base, check=False)
    while result.returncode:
        conflicts = set(git(path, 'diff', '--name-only', '--diff-filter=U').stdout.splitlines())
        if kind != 'server' or not conflicts or not conflicts <= GENERATED:
            raise RuntimeError(f"Source conflict preserved in {path}: {', '.join(sorted(conflicts)) or result.stdout}. No branches were published.")
        # Generated contracts are rebuilt from the already merged source. Never
        # choose a side automatically for application code or authored docs.
        git(path, 'restore', '--ours', '--worktree', '--', *sorted(conflicts))
        command(['swag', 'init', '-g', 'cmd/beacon/main.go', '-o', 'docs', '--parseInternal', '--parseDependency'], cwd=path)
        git(path, 'add', '--', *sorted(GENERATED))
        result = git(path, '-c', 'core.editor=true', 'rebase', '--continue', check=False)


def validate(path, cache):
    if git(path, 'status', '--porcelain').stdout:
        raise RuntimeError(f'Dirty worktree preserved: {path}')
    versions = command(['go', 'version'], cwd=path).stdout.strip() + ' / ' + command(['swag', '--version'], cwd=path).stdout.strip()
    build_environment = command(['go', 'env', '-json', 'GOOS', 'GOARCH', 'CGO_ENABLED', 'GOFLAGS', 'GOWORK'], cwd=path).stdout.strip()
    tree = git(path, 'rev-parse', 'HEAD^{tree}').stdout.strip()
    receipt = cache / (tree + '.json')
    if receipt.exists():
        record = json.loads(receipt.read_text(encoding='utf-8'))
        if record['tools'] == versions and record.get('build_environment') == build_environment and record['passed']:
            return dict(tree=tree, reused=True, receipt=str(receipt))
    logdir = cache / tree
    logdir.mkdir(parents=True, exist_ok=True)
    command(['swag', 'init', '-g', 'cmd/beacon/main.go', '-o', 'docs', '--parseInternal', '--parseDependency'], cwd=path, log=logdir/'swagger.txt')
    changed = set(git(path, 'diff', '--name-only').stdout.splitlines())
    if changed:
        if not changed <= GENERATED:
            raise RuntimeError('Unexpected non-generated changes during validation')
        git(path, 'add', '--', *sorted(GENERATED))
        git(path, 'commit', '-m', 'docs(api): refresh generated contract after stack update')
        tree = git(path, 'rev-parse', 'HEAD^{tree}').stdout.strip()
        receipt = cache / (tree + '.json')
    git(path, 'diff', '--check', 'origin/dev...HEAD')
    if command(['gofmt', '-l', '.'], cwd=path).stdout.strip():
        raise RuntimeError('Unformatted Go files; correct them before publishing')
    for name, args in [('build', ['go', 'build', './...']), ('vet', ['go', 'vet', './...']), ('tests', ['go', 'test', './...'])]:
        command(args, cwd=path, log=logdir/(name+'.txt'))
    write(receipt, dict(passed=True, tree=tree, tools=versions, build_environment=build_environment, logs=str(logdir)))
    return dict(tree=tree, reused=False, receipt=str(receipt))


def web_fingerprint(path):
    settings = {key: value for key, value in ENV.items() if key.startswith('VITE_') or key in ('NODE_ENV', 'NODE_OPTIONS')}
    for name in ('.env', '.env.local', '.env.production', '.env.production.local'):
        if (path/name).is_file():
            settings[name] = hashlib.sha256((path/name).read_bytes()).hexdigest()
    return hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()


def validate_web(path, cache):
    if git(path, 'status', '--porcelain').stdout:
        raise RuntimeError(f'Dirty worktree preserved: {path}')
    npm = shutil.which('npm.cmd' if os.name == 'nt' else 'npm')
    if not npm:
        raise RuntimeError('npm is unavailable')
    versions = command(['node', '--version'], cwd=path).stdout.strip() + ' / ' + command([npm, '--version'], cwd=path).stdout.strip() + ' / ' + command(['node', '-p', 'process.platform+"/"+process.arch'], cwd=path).stdout.strip()
    tree = git(path, 'rev-parse', 'HEAD^{tree}').stdout.strip()
    fingerprint = web_fingerprint(path)
    receipt = cache/(tree+'.json')
    if receipt.exists():
        record = json.loads(receipt.read_text(encoding='utf-8'))
        if record.get('tools') == versions and record.get('build_environment') == fingerprint and record['passed']:
            return dict(tree=tree, reused=True, receipt=str(receipt))
    logs = cache/tree; logs.mkdir(parents=True, exist_ok=True)
    modules = path/'node_modules'
    if not modules.resolve().is_relative_to(path.resolve()):
        raise RuntimeError('Refusing to replace dependencies linked outside this worktree')
    lock = hashlib.sha256((path/'package-lock.json').read_bytes()).hexdigest()
    marker = modules/'.beacon-lock-sha256'
    if not marker.exists() or marker.read_text() != lock:
        command([npm, 'ci', '--no-audit', '--no-fund'], cwd=path, log=logs/'install.txt')
        marker.write_text(lock)
    git(path, 'diff', '--check', 'origin/dev...HEAD')
    for name, arguments in [('build', ['run', 'build']), ('lint', ['run', 'lint']), ('tests', ['test', '--', '--maxWorkers=2'])]:
        command([npm, *arguments], cwd=path, log=logs/(name+'.txt'))
    write(receipt, dict(passed=True, tree=tree, tools=versions, build_environment=fingerprint, logs=str(logs)))
    return dict(tree=tree, reused=False, receipt=str(receipt))


def preview_tree(repo, head, overlays):
    for overlay in overlays:
        tree = git(repo, 'merge-tree', '--write-tree', head, overlay).stdout.strip()
        head = git(repo, 'commit-tree', tree, '-p', head, '-p', overlay, '-m', 'test: assemble preview source').stdout.strip()
    return git(repo, 'rev-parse', head+'^{tree}').stdout.strip()


def active_overlays(manifest):
    active = []
    seen = {entry['pr'] for entry in manifest['entries']}
    for overlay in manifest.get('preview_overlays', []):
        if isinstance(overlay, str):
            if not re.fullmatch(r'[a-f0-9]{40}', overlay):
                raise RuntimeError('Independent preview boundaries must be exact commit IDs')
            active.append(dict(pr=None, head=overlay))
            continue
        if not isinstance(overlay, dict) or type(overlay.get('pr')) is not int or overlay['pr'] <= 0:
            raise RuntimeError('Independent preview PRs need a positive PR number')
        if not isinstance(overlay.get('head'), str) or not re.fullmatch(r'[a-f0-9]{40}', overlay['head']):
            raise RuntimeError('Independent preview boundaries must be exact commit IDs')
        if overlay['pr'] in seen:
            raise RuntimeError('An independent preview PR is listed more than once or also in the ordered stack')
        seen.add(overlay['pr'])
        pull = json.loads(command(['gh', 'api', f"repos/{manifest['upstream']}/pulls/{overlay['pr']}"]).stdout)
        if pull['base']['ref'] != 'dev':
            raise RuntimeError('Unexpected independent preview PR target; this workflow only targets dev')
        if pull['merged']:
            continue
        if pull['state'] != 'open' or pull['head']['sha'] != overlay['head'] or pull['head']['repo']['full_name'] != manifest['fork']:
            raise RuntimeError(f"An independent preview candidate (PR #{overlay['pr']}) changed; review it before continuing")
        active.append(dict(pr=overlay['pr'], head=overlay['head']))
    return active


def simulate_squash_order(repo, base, entries):
    """Prove the history-only refresh after each earlier squash preserves code."""
    parent = base
    proof = []
    for entry in entries:
        parent_tree = git(repo, 'rev-parse', parent+'^{tree}').stdout.strip()
        delta_base_tree = git(repo, 'rev-parse', entry['base']+'^{tree}').stdout.strip()
        if parent_tree != delta_base_tree:
            raise RuntimeError('Stack parent differs from the reviewed delta base')
        tree = git(repo, 'rev-parse', entry['head']+'^{tree}').stdout.strip()
        # Squashing changes ancestry. A child must drop its accepted parent,
        # even when the source is identical. Here identical parent trees prove
        # this is a topology-only move; refresh performs the real rebase --onto.
        restacked = git(repo, 'commit-tree', tree, '-p', parent, '-m', 'test: simulate history-only stack refresh').stdout.strip()
        merged = git(repo, 'merge-tree', '--write-tree', parent, restacked).stdout.strip()
        if merged != tree:
            raise RuntimeError('Simulated merge did not produce the reviewed candidate tree')
        parent = git(repo, 'commit-tree', tree, '-p', parent, '-m', 'test: simulate reviewed stack squash merge').stdout.strip()
        proof.append(dict(pr=entry['pr'], tree=tree, clean_after_squash_and_refresh=True, source_tree_preserved=True))
    return proof


def main(mode, manifest_path=MANIFEST, state=STATE, branch=None):
    global GUARD_SCRIPT
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('guard_script'):
        GUARD_SCRIPT = str(local_path(manifest['guard_script']))
    if GUARD_SCRIPT and not Path(GUARD_SCRIPT).is_file():
        raise RuntimeError('Configured repository guard is missing; no changes are permitted')
    kind = manifest.get('kind', 'server')
    repo = local_path(manifest['repo'])
    check_remotes(repo, manifest)
    pulls = [json.loads(command(['gh', 'api', f"repos/{manifest['upstream']}/pulls/{e['pr']}"]).stdout) for e in manifest['entries']]
    for pull in pulls:
        if pull['head']['repo']['full_name'] != manifest['fork']:
            raise RuntimeError('Unexpected fork identity')
    entries = active_entries(manifest['entries'], pulls)
    overlays = active_overlays(manifest)
    base = command(['gh', 'api', f"repos/{manifest['upstream']}/commits/dev", '--jq', '.sha']).stdout.strip()
    parent = base
    needs_refresh = False
    for entry in entries:
        needs_refresh = needs_refresh or entry['base'] != parent
        parent = entry['head']
    if mode == 'check':
        if needs_refresh:
            raise RuntimeError('The stack has an outdated parent; refresh before relying on previous checks')
        if any(overlay['pr'] is None for overlay in overlays):
            raise RuntimeError('Independent preview commits need a PR/head record before GitHub checks can be verified')
        results = []
        targets = [(entry, False) for entry in entries] + [(dict(overlay, remote_head=overlay['head']), True) for overlay in overlays]
        for entry, is_overlay in targets:
            result = command(['gh', 'pr', 'checks', str(entry['pr']), '-R', manifest['upstream'],
                              '--json', 'name,state,bucket,link'], check=False)
            checks = json.loads(result.stdout) if result.stdout.lstrip().startswith('[') else []
            passed = result.returncode == 0 and bool(checks) and all(c['bucket'] == 'pass' or (c['bucket'] == 'skipping' and c['name'] in manifest.get('allowed_skips', [])) for c in checks) and any(c['name'] == 'build' and c['bucket'] == 'pass' for c in checks)
            results.append(dict(pr=entry['pr'], head=entry['remote_head'], preview_overlay=is_overlay,
                                source_verified=entry['head'] == entry['remote_head'], passed=passed, checks=checks))
        # A PR-number check can otherwise race with a new push or accepted merge.
        verify_publish_state(manifest, dict(base=base, entries=entries, preview_overlays=overlays))
        write(state/'github-checks.json', results)
        print(json.dumps(results, indent=2))
        if not all(r['source_verified'] and r['passed'] for r in results):
            raise RuntimeError('The current stack still has unpublished changes or incomplete/failing GitHub checks')
        return
    if mode == 'status':
        print(json.dumps(dict(upstream=base, order=[e['pr'] for e in entries], needs_refresh=needs_refresh,
                              preview_overlays=overlays,
                              unverified_overlays=[o['head'] for o in overlays if o['pr'] is None],
                              merged=[e['pr'] for e, p in zip(manifest['entries'], pulls) if p['merged']],
                              unpublished=[e['pr'] for e in entries if e['head'] != e['remote_head']]), indent=2))
        return
    state.mkdir(parents=True, exist_ok=True)
    if mode == 'start':
        if not branch:
            raise RuntimeError('Start requires --branch with a new feature branch name')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', branch):
            raise RuntimeError('Use a plain feature branch name')
        if needs_refresh:
            raise RuntimeError('Refresh the existing stack before starting another dependent change')
        if any(e['head'] != e['remote_head'] for e in entries):
            raise RuntimeError('Publish the prepared stack before starting another dependent change')
        git(repo, 'check-ref-format', '--branch', branch)
        if branch in ('main', 'master', 'dev'):
            raise RuntimeError('Choose a feature branch, not a default or release branch')
        git(repo, 'fetch', 'origin', 'dev')
        if git(repo, 'rev-parse', 'origin/dev').stdout.strip() != base:
            raise RuntimeError('Upstream moved; start again from a fresh snapshot')
        if entries:
            git(repo, 'fetch', manifest['remote'])
        parent = entries[-1]['head'] if entries else base
        path = ROOT/'worktrees'/('feature-'+uuid.uuid4().hex[:10])
        if not path.resolve().is_relative_to(ROOT.resolve()):
            raise RuntimeError('Worktree directory escapes the selected workspace')
        git(repo, 'worktree', 'add', '-b', branch, str(path), parent)
        guard(path, 'Preflight', state/'start-guard.json')
        result = dict(branch=branch, parent=parent, worktree=str(path), depends_on=entries[-1]['pr'] if entries else None)
        write(state/'started.json', result)
        print(json.dumps(result, indent=2))
        return
    if mode in ('refresh', 'sync'):
        git(repo, 'fetch', 'origin', '--prune')
        git(repo, 'fetch', manifest['remote'])
        if git(repo, 'rev-parse', 'origin/dev').stdout.strip() != base:
            raise RuntimeError('Upstream moved during refresh; run it again')
        parent = base
        for entry in entries:
            path = local_path(entry['worktree'])
            common = lambda checkout: (checkout/Path(git(checkout, 'rev-parse', '--git-common-dir').stdout.strip())).resolve()
            if common(path) != common(repo):
                raise RuntimeError('Recorded worktree belongs to a different repository')
            if git(path, 'status', '--porcelain').stdout or git(path, 'rev-parse', 'HEAD').stdout.strip() != entry['head']:
                raise RuntimeError(f"Unrecorded work preserved at {path}; record the intended commit before refreshing")
            if parent != entry['base']:
                suffix = uuid.uuid4().hex[:10]
                path = ROOT/'worktrees'/f"stack-{entry['pr']}-{suffix}"
                if not path.resolve().is_relative_to(ROOT.resolve()):
                    raise RuntimeError('Worktree directory escapes the selected workspace')
                git(repo, 'worktree', 'add', '-b', f"codex/stack-{entry['pr']}-{suffix}", str(path), entry['head'])
                guard(path, 'Preflight', state/f"preflight-{entry['pr']}.json")
                rebase(path, parent, entry['base'], kind)
                entry['worktree'] = str(path)
            else:
                guard(path, 'Preflight', state/f"preflight-{entry['pr']}.json")
            entry['base'] = parent
            entry['validation'] = (validate_web if kind == 'web' else validate)(path, state/'validation')
            entry['head'] = git(path, 'rev-parse', 'HEAD').stdout.strip()
            if entry['head'] == parent:
                raise RuntimeError(f"Open PR #{entry['pr']} has no remaining change; review its closure before publishing")
            parent = entry['head']
            print(f"#{entry['pr']}: {parent[:8]} - {'reused verified tree' if entry['validation']['reused'] else 'checks passed'}", flush=True)
        proof = simulate_squash_order(repo, base, entries)
        # Refresh the independent inputs too, after potentially lengthy builds.
        overlays = active_overlays(manifest)
        combined_tree = preview_tree(repo, parent, [overlay['head'] for overlay in overlays])
        preview = manifest.get('preview', {})
        deployed_tree = preview.get(kind + '_tree', preview.get('server_tree'))
        plan = dict(base=base, entries=entries, preview_overlays=overlays, squash_merge_proof=proof, preview_tree=combined_tree,
                    pi_rebuild_needed=combined_tree != deployed_tree)
        verify_publish_state(manifest, plan)
        write(state/'prepared.json', plan)
        print('Stack merge order verified. Pi rebuild needed: '+str(plan['pi_rebuild_needed']), flush=True)
        if mode == 'refresh':
            return
    else:
        plan = json.loads((state/'prepared.json').read_text(encoding='utf-8'))
    if plan['base'] != base or [e['pr'] for e in plan['entries']] != [e['pr'] for e in entries]:
        raise RuntimeError('Upstream or stack state changed; refresh before publishing')
    pushes = []
    leases = []
    for entry in plan['entries']:
        path = local_path(entry['worktree'])
        if git(path, 'status', '--porcelain').stdout or git(path, 'rev-parse', 'HEAD').stdout.strip() != entry['head']:
            raise RuntimeError('Prepared candidate changed; refresh before publishing')
        if entry['head'] != entry['remote_head']:
            leases.append(f"--force-with-lease=refs/heads/{entry['branch']}:{entry['remote_head']}")
            pushes.append(f"{entry['head']}:refs/heads/{entry['branch']}")
    verify_publish_state(manifest, plan)
    if pushes:
        git(repo, 'push', '--atomic', *leases, manifest['remote'], *pushes)
    for entry in plan['entries']:
        actual = git(repo, 'ls-remote', manifest['remote'], 'refs/heads/'+entry['branch']).stdout.split()[0]
        if actual != entry['head']:
            raise RuntimeError('Published branch verification failed')
        entry['remote_head'] = actual
        guard(entry['worktree'], 'Finish', state/f"finish-{entry['pr']}.json")
    manifest['entries'] = plan['entries']
    write(manifest_path, manifest)
    print(('Published changed branches atomically.' if pushes else 'No branch updates were needed.') + ' Check GitHub CI before merge; no upstream merges were performed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('status', 'start', 'refresh', 'publish', 'sync', 'check'))
    parser.add_argument('--project', choices=('server', 'web'), default='server')
    parser.add_argument('--workspace', type=Path, help='Workspace containing planning, evidence and isolated worktrees')
    parser.add_argument('--manifest', type=Path, help='Explicit stack manifest; repository/worktree paths may be workspace-relative')
    parser.add_argument('--state', type=Path, help='Local validation and prepared-state directory')
    parser.add_argument('--branch', help='New feature branch for Start')
    parser.add_argument('--guard-script', help='Additional PowerShell repository guard; missing/failing guards stop work')
    try:
        args = parser.parse_args()
        if args.workspace:
            ROOT = args.workspace.resolve()
        if args.guard_script:
            GUARD_SCRIPT = args.guard_script
        main(args.mode, args.manifest or ROOT/'planning'/('review-stack-web.json' if args.project == 'web' else 'review-stack.json'),
             args.state or ROOT/'evidence'/('review-stack-web' if args.project == 'web' else 'review-stack'), args.branch)
    except (RuntimeError, OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
