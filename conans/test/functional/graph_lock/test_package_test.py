import textwrap
import unittest

from conans.test.utils.tools import TestClient, GenConanfile


class GraphLockTestPackageTest(unittest.TestCase):
    def augment_test_package_requires(self):
        # https://github.com/conan-io/conan/issues/6067
        client = TestClient()
        client.save({"conanfile.py": GenConanfile().with_name("tool").with_version("0.1")})
        client.run("create .")

        conanfile = textwrap.dedent("""
            from conans import ConanFile 
            class BugTest(ConanFile):
                def test(self):
                    pass
            """)
        client.save({"conanfile.py": GenConanfile().with_name("dep").with_version("0.1"),
                     "test_package/conanfile.py": conanfile,
                     "consumer.txt": "[requires]\ndep/0.1\n",
                     "profile": "[build_requires]\ntool/0.1\n"})

        client.run("export .")
        client.run("graph lock consumer.txt -pr=profile --build missing")

        # Check lock
        client.run("config set general.relax_lockfile=1")
        client.run("create . -pr=profile --lockfile --build missing")
        self.assertIn("tool/0.1:5ab84d6acfe1f23c4fae0ab88f26e3a396351ac9 - Cache", client.out)
        self.assertIn("dep/0.1: Applying build-requirement: tool/0.1", client.out)
        self.assertIn("dep/0.1 (test package): Running test()", client.out)
