import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add depends.py directory to path
DEPENDS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'packages', 'server', 'engine-lib', 'rocketlib-python', 'lib')
)
sys.path.append(DEPENDS_DIR)

# Mock engLib since it's a native/internal module unavailable during pure-python tests
sys.modules['engLib'] = MagicMock()

import depends


class TestDepends(unittest.TestCase):
    @patch('depends.platform.machine')
    @patch('depends.platform.system')
    def test_missing_avx2_non_x86(self, mock_system, mock_machine):
        # If architecture is ARM (e.g. apple silicon without rosetta), it should return False
        # as it doesn't even need to check for AVX2 instructions
        mock_machine.return_value = 'arm64'
        self.assertFalse(depends._is_x86_64_missing_avx2())
        
        mock_machine.return_value = 'aarch64'
        self.assertFalse(depends._is_x86_64_missing_avx2())

    @patch('depends.subprocess.check_output')
    @patch('depends.platform.system')
    @patch('depends.platform.machine')
    def test_missing_avx2_darwin_rosetta(self, mock_machine, mock_system, mock_subprocess):
        mock_machine.return_value = 'x86_64'
        mock_system.return_value = 'Darwin'
        
        # Test case: sysctl returns 0 (missing AVX2)
        mock_subprocess.return_value = '0\n'
        self.assertTrue(depends._is_x86_64_missing_avx2())
        
        # Test case: sysctl returns 1 (has AVX2)
        mock_subprocess.return_value = '1\n'
        self.assertFalse(depends._is_x86_64_missing_avx2())
        
        # Test case: sysctl fails (failsafe to True)
        mock_subprocess.side_effect = Exception("sysctl failed")
        self.assertTrue(depends._is_x86_64_missing_avx2())

    @patch('builtins.open', new_callable=mock_open)
    @patch('depends.platform.system')
    @patch('depends.platform.machine')
    def test_missing_avx2_linux(self, mock_machine, mock_system, mock_file):
        mock_machine.return_value = 'x86_64'
        mock_system.return_value = 'Linux'
        
        # Test case: cpuinfo has avx2
        mock_file.return_value.read.return_value = 'flags: fpu vme de pse tsc msr pae mce cx8 apic sep mtrr pge mca cmov pat pse36 clflush dts acpi mmx fxsr sse sse2 ss ht tm pbe syscall nx pdpe1gb rdtscp lm constant_tsc art arch_perfmon pebs bts rep_good nopl xtopology nonstop_tsc cpuid aperfmperf pni pclmulqdq dtes64 monitor ds_cpl vmx smx est tm2 ssse3 sdbg fma cx16 xtpr pdcm pcid dca sse4_1 sse4_2 x2apic movbe popcnt tsc_deadline_timer aes xsave avx f16c rdrand lahf_lm abm 3dnowprefetch cpuid_fault epb cat_l3 cdp_l3 invpcid_single pti intel_ppin ssbd mba ibrs ibpb stibp tpr_shadow vnmi flexpriority ept vpid ept_ad fsgsbase tsc_adjust bmi1 avx2 smep bmi2 erms invpcid cqm mpx rdt_a avx512f avx512dq rdseed adx smap clflushopt clwb intel_pt avx512cd avx512bw avx512vl xsaveopt xsavec xgetbv1 xsaves cqm_llc cqm_occup_llc cqm_mbm_total cqm_mbm_local dtherm ida arat pln pts pku ospke md_clear pconfig stibp_always_on flush_l1d arch_capabilities'
        self.assertFalse(depends._is_x86_64_missing_avx2())
        
        # Test case: cpuinfo does not have avx2
        mock_file.return_value.read.return_value = 'flags: fpu vme de pse tsc'
        self.assertTrue(depends._is_x86_64_missing_avx2())
        
        # Test case: file open fails
        mock_file.side_effect = Exception("Permission denied")
        self.assertTrue(depends._is_x86_64_missing_avx2())

    @patch.dict('sys.modules', {'ctypes': MagicMock()})
    @patch('depends.platform.system')
    @patch('depends.platform.machine')
    def test_missing_avx2_windows(self, mock_machine, mock_system):
        mock_machine.return_value = 'AMD64' # Windows uses AMD64
        mock_system.return_value = 'Windows'
        
        # Test case: kernel32.IsProcessorFeaturePresent(40) returns True
        import sys
        mock_ctypes = sys.modules['ctypes']
        mock_kernel32 = MagicMock()
        mock_kernel32.IsProcessorFeaturePresent.return_value = True
        mock_ctypes.windll.kernel32 = mock_kernel32
        
        self.assertFalse(depends._is_x86_64_missing_avx2())
        
        # Test case: returns False
        mock_kernel32.IsProcessorFeaturePresent.return_value = False
        self.assertTrue(depends._is_x86_64_missing_avx2())
        
        # Test case: ctypes fails
        mock_ctypes.windll.kernel32.IsProcessorFeaturePresent.side_effect = Exception("Failed")
        self.assertTrue(depends._is_x86_64_missing_avx2())

if __name__ == '__main__':
    unittest.main()
