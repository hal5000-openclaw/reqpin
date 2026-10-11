import json, os, subprocess, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import reqpin

def kinds(text, **kw):
    return [(p["line"], p["kind"]) for p in reqpin.check_text(text, **kw)]

class T(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(kinds("requests==2.31.0\nflask == 3.0\n"), [])
    def test_unpinned(self):
        self.assertEqual(kinds("requests\nflask>=2\n"), [(1, "unpinned"), (2, "unpinned")])
    def test_wildcard_not_pinned_ok_range(self):
        self.assertEqual(kinds("a~=1.2\n"), [(1, "unpinned")])
    def test_comments_blank(self):
        self.assertEqual(kinds("# hi\n\nrequests==1  # note\n"), [])
    def test_includes_ignored(self):
        self.assertEqual(kinds("-r base.txt\n--requirement=x.txt\n-c c.txt\n-i https://x/simple\n"), [])
    def test_extras_markers(self):
        self.assertEqual(kinds('requests[security]==2.0 ; python_version<"3.9"\n'), [])
        self.assertEqual(kinds('requests[security] ; sys_platform=="win32"\n'), [(1, "unpinned")])
    def test_vcs_url(self):
        t = "git+https://github.com/a/b.git@abc#egg=b\n-e git+https://x/y.git#egg=y\npkg @ https://x/p.whl\nhttps://x/q.zip\n"
        self.assertEqual(kinds(t), [])
    def test_duplicates(self):
        self.assertEqual(kinds("Foo_Bar==1\nfoo-bar==2\n"), [(2, "duplicate")])
    def test_duplicate_different_markers_ok(self):
        self.assertEqual(kinds('a==1; os_name=="nt"\na==2; os_name=="posix"\n'), [])
    def test_bad_line(self):
        self.assertEqual(kinds("==1.0\nfoo===\nfoo bar baz\n"), [(1, "bad-line"), (2, "bad-line"), (3, "bad-line")])
    def test_hashes(self):
        t = "a==1 \\\n    --hash=sha256:abc\nb==2\n"
        self.assertEqual(kinds(t, require_hashes=True), [(3, "missing-hash")])
        self.assertEqual(kinds(t), [])
    def test_cli_exit_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "r.txt")
            open(p, "w").write("requests\n")
            r = subprocess.run([sys.executable, reqpin.__file__, "--json", p], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertEqual(json.loads(r.stdout)["total"], 1)
            open(p, "w").write("requests==1\n")
            self.assertEqual(subprocess.run([sys.executable, reqpin.__file__, p], capture_output=True).returncode, 0)

if __name__ == "__main__":
    unittest.main()
