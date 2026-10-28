import unittest
from portable_checks import verify_flags


class PortableChecks(unittest.TestCase):
    def test_accept_supported_non_native_avx2(self):
        commands = [{'file': '/source/ggml/src/ggml-cpu/ggml-cpu.cpp',
                     'command': 'c++ -march=x86-64 -mtune=generic -mavx -mavx2 -mfma -mf16c -mbmi2 -msse4.2 -c cpu.cpp'}]
        result = verify_flags(commands, {'avx', 'avx2', 'fma', 'f16c', 'bmi2', 'sse4_2'})
        self.assertTrue(result['passed'])

    def test_reject_native_or_unsupported_instruction_switch(self):
        for switch in ['-march=native', '-march=znver3', '-mavx512f', '-mamx-tile']:
            with self.subTest(switch=switch), self.assertRaises(RuntimeError):
                verify_flags([{'file': '/ggml-cpu/cpu.cpp', 'command': 'c++ '+switch}], {'avx2'})

    def test_reject_missing_host_feature_and_missing_backend(self):
        with self.assertRaises(RuntimeError):
            verify_flags([{'file':'/ggml-cpu/cpu.cpp','command':'c++ -mavx2'}], {'avx'})
        with self.assertRaises(RuntimeError):
            verify_flags([{'file':'/server.cpp','command':'c++'}], {'avx2'})


if __name__ == '__main__':
    unittest.main()
