"""Offline regression checks for the local stack helper; no GitHub/Pi access."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import beacon_stack as stack


class PreviewCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='beacon-preview-check-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = dict(repo='unused', upstream='MeshCore-Beacon/beacon-web',
            fork='example/beacon-web', remote='contribution', entries=[
                dict(pr=1, branch='codex/one', base='a'*40, head='b'*40, remote_head='b'*40)],
            preview_overlays=[dict(pr=2, head='c'*40)])
        self.pulls = {number: dict(merged=False, state='open', base=dict(ref='dev'),
            head=dict(sha=head, ref='codex/one', repo=dict(full_name='example/beacon-web')))
            for number, head in ((1, 'b'*40), (2, 'c'*40))}
        self.checks = {number: [dict(name='build', state='SUCCESS', bucket='pass', link='https://example.invalid/check')]
                       for number in (1, 2)}
        self.commands = []
        self.on_checks = lambda number: None

    def command(self, args, **kwargs):
        self.commands.append(args)
        if args[:2] == ['gh', 'api']:
            output = 'a'*40 if args[2].endswith('/commits/dev') else json.dumps(self.pulls[int(args[2].split('/')[-1])])
            return subprocess.CompletedProcess(args, 0, output)
        if args[:3] == ['gh', 'pr', 'checks']:
            number = int(args[3])
            checks = self.checks[number]
            code = 0 if all(c['bucket'] in ('pass', 'skipping') for c in checks) else 1
            self.on_checks(number)
            return subprocess.CompletedProcess(args, code, json.dumps(checks))
        raise AssertionError(f'Unexpected external command: {args}')

    def run_main(self, mode='check'):
        path = self.root/'manifest.json'
        stack.write(path, self.manifest)
        output = io.StringIO()
        with patch.object(stack, 'GUARD_SCRIPT', None), patch.object(stack, 'check_remotes'), \
             patch.object(stack, 'command', side_effect=self.command), redirect_stdout(output):
            stack.main(mode, path, self.root/'state')
        return json.loads(output.getvalue())

    def test_failed_overlay_prevents_a_green_check(self):
        self.checks[2][0].update(state='FAILURE', bucket='fail')
        with self.assertRaisesRegex(RuntimeError, 'incomplete/failing'):
            self.run_main()

    def test_changed_overlay_stops_check(self):
        self.pulls[2]['head']['sha'] = 'd'*40
        with self.assertRaisesRegex(RuntimeError, 'independent preview'):
            self.run_main()

    def test_check_reports_the_overlay_and_ordered_pr(self):
        rows = self.run_main()
        self.assertEqual({row['pr'] for row in rows}, {1, 2})
        self.assertTrue(all(row['passed'] and row['source_verified'] for row in rows))
        self.assertEqual({row['pr'] for row in rows if row['preview_overlay']}, {2})

    def test_pending_or_missing_overlay_checks_fail(self):
        for checks in ([], [dict(name='build', state='PENDING', bucket='pending')]):
            with self.subTest(checks=checks):
                self.checks[2] = checks
                with self.assertRaisesRegex(RuntimeError, 'incomplete/failing'):
                    self.run_main()

    def test_overlay_uses_the_explicit_skip_policy_and_requires_a_build(self):
        self.checks[2].append(dict(name='Analyze', state='SKIPPED', bucket='skipping'))
        with self.assertRaisesRegex(RuntimeError, 'incomplete/failing'):
            self.run_main()
        self.manifest['allowed_skips'] = ['Analyze']
        self.assertTrue(all(row['passed'] for row in self.run_main()))
        self.checks[2] = self.checks[2][1:]
        with self.assertRaisesRegex(RuntimeError, 'incomplete/failing'):
            self.run_main()

    def test_a_failed_check_command_cannot_pass_from_partial_output(self):
        original = self.command
        def failed_command(args, **kwargs):
            result = original(args, **kwargs)
            if args[:4] == ['gh', 'pr', 'checks', '2']:
                result.returncode = 1
            return result
        with patch.object(self, 'command', side_effect=failed_command):
            with self.assertRaisesRegex(RuntimeError, 'incomplete/failing'):
                self.run_main()

    def test_merged_overlay_is_dropped_but_unmerged_closure_stops(self):
        self.pulls[2].update(merged=True, state='closed')
        self.assertEqual([row['pr'] for row in self.run_main()], [1])
        self.assertNotIn(['gh', 'pr', 'checks', '2'], [c[:4] for c in self.commands])
        self.pulls[2]['merged'] = False
        with self.assertRaisesRegex(RuntimeError, 'independent preview'):
            self.run_main()

    def test_wrong_overlay_fork_or_base_stops(self):
        self.pulls[2]['head']['repo']['full_name'] = 'unexpected/beacon-web'
        with self.assertRaisesRegex(RuntimeError, 'independent preview'):
            self.run_main()
        self.pulls[2]['head']['repo']['full_name'] = self.manifest['fork']
        self.pulls[2]['base']['ref'] = 'main'
        with self.assertRaisesRegex(RuntimeError, 'target'):
            self.run_main()

    def test_status_lists_independent_inputs_and_stops_on_drift(self):
        result = self.run_main('status')
        self.assertEqual(result['preview_overlays'], [dict(pr=2, head='c'*40)])
        self.pulls[2]['head']['sha'] = 'd'*40
        with self.assertRaisesRegex(RuntimeError, 'independent preview'):
            self.run_main('status')

    def test_unlinked_commits_are_visible_but_cannot_receive_a_green_check(self):
        self.manifest['preview_overlays'] = ['c'*40]
        status = self.run_main('status')
        self.assertEqual(status['unverified_overlays'], ['c'*40])
        with self.assertRaisesRegex(RuntimeError, 'PR/head record'):
            self.run_main()

    def test_invalid_or_duplicate_overlay_records_stop_before_checks(self):
        for overlays in (['--exec=untrusted'], [dict(pr=2, head='HEAD')],
                         [dict(pr=True, head='c'*40)], [dict(pr=2, head=None)],
                         [dict(pr=1, head='b'*40)], [dict(pr=2, head='c'*40)]*2):
            with self.subTest(overlays=overlays):
                self.manifest['preview_overlays'] = overlays
                self.commands.clear()
                with self.assertRaises(RuntimeError):
                    self.run_main()
                self.assertFalse(any(c[:3] == ['gh', 'pr', 'checks'] for c in self.commands))

    def test_a_push_during_checks_is_detected_for_both_kinds_of_pr(self):
        for number in (1, 2):
            with self.subTest(number=number):
                original = self.pulls[number]['head']['sha']
                def push(checked):
                    if checked == 2:
                        self.pulls[number]['head']['sha'] = 'd'*40
                self.on_checks = push
                with self.assertRaisesRegex(RuntimeError, 'changed'):
                    self.run_main()
                self.pulls[number]['head']['sha'] = original

    def test_publication_requires_the_same_independent_inputs_as_preparation(self):
        plan = dict(base='a'*40, entries=self.manifest['entries'], preview_overlays=[dict(pr=2, head='c'*40)])
        with patch.object(stack, 'command', side_effect=self.command):
            stack.verify_publish_state(self.manifest, plan)
            # Old prepared files cannot silently omit an active overlay.
            with self.assertRaisesRegex(RuntimeError, 'preview overlays changed'):
                stack.verify_publish_state(self.manifest, dict(base=plan['base'], entries=plan['entries']))
            self.pulls[2]['merged'] = True
            with self.assertRaisesRegex(RuntimeError, 'preview overlays changed'):
                stack.verify_publish_state(self.manifest, plan)
            self.pulls[2]['merged'] = False
            self.pulls[2]['head']['sha'] = 'd'*40
            with self.assertRaisesRegex(RuntimeError, 'independent preview'):
                stack.verify_publish_state(self.manifest, plan)


class StackTests(unittest.TestCase):
    def test_missing_configured_guard_stops_before_commands(self):
        with tempfile.TemporaryDirectory(prefix='beacon-missing-guard-') as directory:
            root = Path(directory); manifest = root/'stack.json'
            stack.write(manifest, dict(guard_script=str(root/'missing.ps1')))
            with patch.object(stack, 'GUARD_SCRIPT', None), patch.object(stack, 'command', side_effect=AssertionError('must stop before commands')):
                with self.assertRaisesRegex(RuntimeError, 'guard is missing'):
                    stack.main('start', manifest, root/'state', branch='codex/next')

    def test_publication_rechecks_upstream_after_validation(self):
        manifest = dict(upstream='MeshCore-Beacon/beacon-web', fork='example/beacon-web', entries=[])
        class Result:
            stdout = 'new-upstream'
        with patch.object(stack, 'command', return_value=Result()):
            with self.assertRaisesRegex(RuntimeError, 'changed during validation'):
                stack.verify_publish_state(manifest, dict(base='old-upstream', entries=[]))
            stack.verify_publish_state(manifest, dict(base='new-upstream', entries=[]))

    def test_portable_guard_rejects_default_and_dirty_branches(self):
        with tempfile.TemporaryDirectory(prefix='beacon-guard-test-') as directory:
            repo = Path(directory); self.init_repo(repo); self.commit(repo, 'file.txt', 'base\n')
            stack.git(repo, 'checkout', '-B', 'dev')
            with patch.object(stack, 'GUARD_SCRIPT', None):
                with self.assertRaisesRegex(RuntimeError, 'isolated feature branch'):
                    stack.guard(repo, 'Preflight', repo/'receipt.json')
                stack.git(repo, 'checkout', '-b', 'codex/feature')
                (repo/'file.txt').write_text('dirty\n')
                with self.assertRaisesRegex(RuntimeError, 'isolated feature branch'):
                    stack.guard(repo, 'Preflight', repo/'receipt.json')

    def test_start_after_all_merges_uses_current_dev_without_rebase_or_build(self):
        with tempfile.TemporaryDirectory(prefix='beacon-start-test-') as directory:
            root = Path(directory); repo = root/'repo'; repo.mkdir(); self.init_repo(repo)
            old = self.commit(repo, 'file.txt', 'old\n')
            current = self.commit(repo, 'file.txt', 'accepted\n')
            stack.git(repo, 'remote', 'add', 'origin', 'https://github.com/MeshCore-Beacon/beacon-web.git')
            stack.git(repo, 'remote', 'add', 'contribution', 'https://github.com/example/beacon-web.git')
            stack.git(repo, 'update-ref', 'refs/remotes/origin/dev', current)
            manifest = root/'stack.json'
            stack.write(manifest, dict(repo='repo', upstream='MeshCore-Beacon/beacon-web', fork='example/beacon-web', remote='contribution', entries=[dict(pr=1, branch='codex/old', head=old, remote_head=old, base=old, worktree='repo')]))
            original = stack.command
            class Result:
                returncode = 0
                stdout = ''
            def fake_command(args, **kwargs):
                if args[0] == 'gh':
                    r = Result()
                    r.stdout = current if 'commits/dev' in args[2] else json.dumps(dict(merged=True, head=dict(repo=dict(full_name='example/beacon-web'))))
                    return r
                if args[:2] == ['git', 'fetch']:
                    return Result()
                if args[0] in ('npm', 'node', 'go', 'swag') or args[:2] == ['git', 'rebase']:
                    raise AssertionError('A fresh phase must not rebase or build')
                return original(args, **kwargs)
            with patch.object(stack, 'ROOT', root), patch.object(stack, 'GUARD_SCRIPT', None), patch.object(stack, 'command', fake_command):
                stack.main('start', manifest, root/'state', branch='codex/next')
            started = json.loads((root/'state/started.json').read_text())
            self.assertEqual(started['parent'], current)
            self.assertIsNone(started['depends_on'])
            self.assertEqual(stack.git(started['worktree'], 'rev-parse', 'HEAD').stdout.strip(), current)

    def test_remote_updates_and_closed_prs_stop_publication(self):
        entries = [dict(pr=1, branch='codex/one', remote_head='1'*40, head='1'*40, base='2'*40)]
        pull = dict(merged=False, state='open', head=dict(sha='1'*40, ref='codex/one'), base=dict(ref='dev'))
        self.assertEqual(len(stack.active_entries(entries, [pull])), 1)
        for changed in [dict(pull, state='closed'), dict(pull, head=dict(sha='someone-elses-work', ref='codex/one'))]:
            with self.assertRaises(RuntimeError):
                stack.active_entries(entries, [changed])
        self.assertEqual(stack.active_entries(entries, [dict(pull, merged=True, state='closed')]), [])
        with self.assertRaisesRegex(RuntimeError, 'exact commit IDs'):
            stack.active_entries([dict(entries[0], base='--exec=untrusted')], [pull])

    def test_squash_merges_then_drop_accepted_parent(self):
        with tempfile.TemporaryDirectory(prefix='beacon-stack-test-') as directory:
            repo = Path(directory)
            self.init_repo(repo)
            base = self.commit(repo, 'settings.go', 'base\n')
            first = self.commit(repo, 'settings.go', 'base\naccounts\n')
            second = self.commit(repo, 'settings.go', 'base\naccounts\nbackup\n')
            entries = [dict(pr=1, head=first, base=base), dict(pr=2, head=second, base=first)]
            proof = stack.simulate_squash_order(repo, base, entries)
            self.assertTrue(all(row['clean_after_squash_and_refresh'] for row in proof))
            tree = stack.git(repo, 'rev-parse', first+'^{tree}').stdout.strip()
            squash = stack.git(repo, 'commit-tree', tree, '-p', base, '-m', 'accepted first PR').stdout.strip()
            stack.git(repo, 'checkout', '-b', 'child', second)
            stack.rebase(repo, squash, first)
            self.assertEqual(stack.git(repo, 'rev-parse', 'HEAD^{tree}').stdout.strip(), proof[-1]['tree'])
            self.assertEqual(stack.git(repo, 'rev-list', '--count', squash+'..HEAD').stdout.strip(), '1')

    def test_source_conflict_is_left_for_review(self):
        with tempfile.TemporaryDirectory(prefix='beacon-stack-test-') as directory:
            repo = Path(directory)
            self.init_repo(repo)
            base = self.commit(repo, 'main.go', 'base\n')
            child = self.commit(repo, 'main.go', 'our change\n')
            stack.git(repo, 'checkout', '-b', 'upstream', base)
            upstream = self.commit(repo, 'main.go', 'different upstream change\n')
            stack.git(repo, 'checkout', '-b', 'candidate', child)
            with self.assertRaisesRegex(RuntimeError, 'Source conflict preserved'):
                stack.rebase(repo, upstream, base)
            self.assertEqual(stack.git(repo, 'diff', '--name-only', '--diff-filter=U').stdout.strip(), 'main.go')
            self.assertEqual(stack.git(repo, 'rev-parse', 'refs/heads/candidate').stdout.strip(), child)
            stack.git(repo, 'rebase', '--abort')

    def test_verified_tree_skips_builds(self):
        with tempfile.TemporaryDirectory(prefix='beacon-stack-cache-') as directory:
            cache = Path(directory)
            stack.write(cache/'tree.json', dict(passed=True, tools='go / swag', build_environment='{}'))
            class Result:
                stdout = ''
            def fake_git(repo, *args, **kwargs):
                result = Result()
                result.stdout = 'tree\n' if args[0] == 'rev-parse' else ''
                return result
            def fake_command(args, **kwargs):
                if args[:2] == ['go', 'env']:
                    result = Result(); result.stdout = '{}'; return result
                if args not in (['go', 'version'], ['swag', '--version']):
                    raise AssertionError('cached source tree unexpectedly rebuilt')
                result = Result(); result.stdout = args[0]
                return result
            with patch.object(stack, 'git', fake_git), patch.object(stack, 'command', fake_command):
                self.assertTrue(stack.validate(cache, cache)['reused'])

    def test_web_environment_fingerprint_changes_without_recording_values(self):
        with tempfile.TemporaryDirectory(prefix='beacon-web-cache-') as directory:
            root = Path(directory)
            first = stack.web_fingerprint(root)
            (root/'.env.local').write_text('VITE_FIXTURE=PRIVATE_CANARY\n', encoding='utf-8')
            second = stack.web_fingerprint(root)
            self.assertNotEqual(first, second)
            self.assertNotIn('PRIVATE_CANARY', second)
            self.assertEqual(len(second), 64)

    def test_preview_overlay_preserves_both_independent_changes(self):
        with tempfile.TemporaryDirectory(prefix='beacon-preview-test-') as directory:
            repo = Path(directory); self.init_repo(repo)
            base = self.commit(repo, 'base.txt', 'base\n')
            feature = self.commit(repo, 'analytics.txt', 'charts\n')
            stack.git(repo, 'checkout', '-b', 'overlay', base)
            overlay = self.commit(repo, 'nodes.txt', 'badges\n')
            tree = stack.preview_tree(repo, feature, [overlay])
            self.assertEqual(set(stack.git(repo, 'ls-tree', '--name-only', tree).stdout.splitlines()), {'base.txt', 'analytics.txt', 'nodes.txt'})

    @staticmethod
    def init_repo(repo):
        stack.git(repo, 'init', '-q')
        stack.git(repo, 'config', 'user.name', 'Stack test')
        stack.git(repo, 'config', 'user.email', 'test@example.invalid')
        stack.git(repo, 'config', 'core.autocrlf', 'false')

    @staticmethod
    def commit(repo, file, text):
        (repo/file).write_text(text, encoding='utf-8', newline='\n')
        stack.git(repo, 'add', file)
        stack.git(repo, 'commit', '-q', '-m', text.strip().replace('\n', ' '))
        return stack.git(repo, 'rev-parse', 'HEAD').stdout.strip()


if __name__ == '__main__':
    unittest.main()
