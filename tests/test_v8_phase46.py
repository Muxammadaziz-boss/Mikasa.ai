# ========== tests/test_v8_phase46.py ==========
# Phase 46 — Real Remote Tool Execution — Security Tests

import os
import sys
import time
import unittest
import asyncio
import json
import ast

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from agent.tools import PathSecurityValidator, AgentToolRegistry, AgentToolHandler, ALLOWED_APPS, PROTECTED_PROCESSES
except ImportError:
    PathSecurityValidator = None
    AgentToolRegistry = None
    AgentToolHandler = None
    ALLOWED_APPS = {}
    PROTECTED_PROCESSES = set()

try:
    from agent.executor import RemoteCommandExecutor, CommandPoller, CommandStatus, CommandResult
except ImportError:
    RemoteCommandExecutor = None
    CommandPoller = None
    CommandStatus = None
    CommandResult = None

try:
    from core.v8.command_queue import CommandQueueManager, CommandState, QueuedCommand, ConfirmationToken
except ImportError:
    CommandQueueManager = None
    CommandState = None
    QueuedCommand = None
    ConfirmationToken = None

try:
    from core.v8.remote_tools import RemoteToolDefinition, RemoteToolRegistry
except ImportError:
    RemoteToolDefinition = None
    RemoteToolRegistry = None

try:
    from core.v8.events import RemoteEventType
except ImportError:
    RemoteEventType = None


def _reset_singletons():
    """Barcha singleton instancelarni tozalash"""
    if AgentToolRegistry and hasattr(AgentToolRegistry, '_instance'):
        AgentToolRegistry._instance = None
    if CommandQueueManager and hasattr(CommandQueueManager, '_default_instance'):
        CommandQueueManager._default_instance = None
    if RemoteToolRegistry and hasattr(RemoteToolRegistry, '_default_instance'):
        RemoteToolRegistry._default_instance = None


# ================================================================
# 1. PATH SECURITY VALIDATOR TESTS (8 tests)
# ================================================================
class TestPathSecurityValidator(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_valid_sandbox_path(self):
        """Sandbox ichidagi yo'l muvaffaqiyatli o'tishi kerak"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        sandbox = PathSecurityValidator.get_default_sandbox()
        os.makedirs(sandbox, exist_ok=True)
        valid_path = os.path.join(sandbox, "test.txt")
        is_valid, resolved, err = PathSecurityValidator.validate_path(valid_path)
        self.assertTrue(is_valid, f"Sandbox path should be valid, got error: {err}")

    def test_path_traversal_blocked(self):
        """'..' bilan path traversal bloklangan bo'lishi kerak"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        is_valid, _, err = PathSecurityValidator.validate_path("../../../etc/passwd")
        self.assertFalse(is_valid)
        self.assertEqual(err, "PATH_TRAVERSAL")

    def test_unc_path_blocked(self):
        r"""\\server\share UNC yo'l bloklangan bo'lishi kerak"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        is_valid, _, err = PathSecurityValidator.validate_path(r"\\server\share\file.txt")
        self.assertFalse(is_valid)
        self.assertEqual(err, "UNC_PATH_BLOCKED")

    def test_device_name_blocked(self):
        """Windows device nomlari (CON, NUL, COM1, LPT1) bloklangan"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        sandbox = PathSecurityValidator.get_default_sandbox()
        os.makedirs(sandbox, exist_ok=True)
        for dev in ["CON", "NUL", "COM1", "LPT1"]:
            path = os.path.join(sandbox, dev)
            is_valid, _, err = PathSecurityValidator.validate_path(path)
            self.assertFalse(is_valid, f"{dev} should be blocked")
            self.assertEqual(err, "DEVICE_NAME_BLOCKED", f"{dev} should give DEVICE_NAME_BLOCKED")

    def test_sensitive_directory_blocked(self):
        """C:\\Windows kabi sezgir kataloglar bloklangan"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        is_valid, _, err = PathSecurityValidator.validate_path(r"C:\Windows\System32\cmd.exe")
        self.assertFalse(is_valid)
        self.assertEqual(err, "SENSITIVE_DIRECTORY")

    def test_credential_file_blocked(self):
        """Credential fayllar (.env, id_rsa) bloklangan"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        sandbox = PathSecurityValidator.get_default_sandbox()
        os.makedirs(sandbox, exist_ok=True)
        for cred in [".env", "id_rsa"]:
            path = os.path.join(sandbox, cred)
            is_valid, _, err = PathSecurityValidator.validate_path(path)
            self.assertFalse(is_valid, f"{cred} should be blocked")
            self.assertEqual(err, "CREDENTIAL_FILE", f"{cred} should give CREDENTIAL_FILE")

    def test_path_outside_sandbox(self):
        """Sandbox tashqarisidagi yo'l rad etilishi kerak"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        is_valid, _, err = PathSecurityValidator.validate_path(r"C:\Users\Public\somefile.txt")
        self.assertFalse(is_valid)
        self.assertEqual(err, "PATH_OUTSIDE_SANDBOX")

    def test_empty_path_rejected(self):
        """Bo'sh yo'l rad etilishi kerak"""
        if not PathSecurityValidator: self.skipTest("Module not found")
        is_valid, _, err = PathSecurityValidator.validate_path("")
        self.assertFalse(is_valid)
        self.assertEqual(err, "EMPTY_PATH")


# ================================================================
# 2. AGENT TOOL REGISTRY TESTS (7 tests)
# ================================================================
class TestAgentToolRegistry(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_registry_singleton(self):
        """get_default_instance() har doim bir xil instance qaytaradi"""
        if not AgentToolRegistry: self.skipTest("Module not found")
        reg1 = AgentToolRegistry.get_default_instance()
        reg2 = AgentToolRegistry.get_default_instance()
        self.assertIs(reg1, reg2)

    def test_all_15_tools_registered(self):
        """Aniq 15 ta tool ro'yxatdan o'tgan bo'lishi kerak"""
        if not AgentToolRegistry: self.skipTest("Module not found")
        reg = AgentToolRegistry.get_default_instance()
        tools = reg.list_tools()
        self.assertEqual(len(tools), 15, f"Expected 15 tools, got {len(tools)}: {tools}")

    def test_tool_ids_match(self):
        """Barcha kutilgan tool ID lar mavjud"""
        if not AgentToolRegistry: self.skipTest("Module not found")
        reg = AgentToolRegistry.get_default_instance()
        tools = reg.list_tools()
        expected = [
            "system.status", "system.info", "system.screenshot",
            "app.list", "app.launch", "app.close",
            "file.list", "file.read", "file.write", "file.delete",
            "network.info",
            "power.restart", "power.shutdown", "power.sleep", "power.wake"
        ]
        for tid in expected:
            self.assertIn(tid, tools, f"Tool {tid} not found in registry")

    def test_system_status_handler(self):
        """system.status handler ishlashi kerak"""
        if not AgentToolRegistry: self.skipTest("Module not found")
        reg = AgentToolRegistry.get_default_instance()
        result = reg.execute("system.status", {})
        self.assertTrue(result.get("ok"), f"system.status failed: {result}")
        self.assertIn("status", result.get("data", {}))

    def test_app_launch_allowed(self):
        """notepad ALLOWED_APPS da bor"""
        if not ALLOWED_APPS: self.skipTest("Module not found")
        self.assertIn("notepad", ALLOWED_APPS)
        self.assertEqual(ALLOWED_APPS["notepad"], "notepad.exe")

    def test_app_launch_blocked(self):
        """cmd.exe ALLOWED_APPS da yo'q"""
        if not ALLOWED_APPS: self.skipTest("Module not found")
        self.assertNotIn("cmd", ALLOWED_APPS)
        self.assertNotIn("cmd.exe", ALLOWED_APPS)
        self.assertNotIn("powershell", ALLOWED_APPS)

    def test_file_read_sandbox(self):
        """Sandbox tashqarisidagi fayl o'qish xatolik qaytaradi"""
        if not AgentToolRegistry: self.skipTest("Module not found")
        reg = AgentToolRegistry.get_default_instance()
        handler = reg.get("file.read")
        if not handler: self.skipTest("file.read handler not found")
        result = handler.handler({"path": r"C:\Windows\win.ini"})
        self.assertFalse(result.get("success", True), "Should block reading outside sandbox")


# ================================================================
# 3. REMOTE COMMAND EXECUTOR TESTS (8 tests)
# ================================================================
class TestRemoteCommandExecutor(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_idempotency(self):
        """Bir xil command_id bilan ikkinchi so'rov cached natija qaytaradi"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            cmd = {
                "command_id": "cmd_idemp",
                "tool_id": "system.status",
                "params": {},
                "nonce": "n_idemp_1",
                "expires_at": time.time() + 300,
            }
            res1 = await executor.execute(cmd)
            res2 = await executor.execute(cmd)
            self.assertEqual(res1['command_id'], res2['command_id'])
            self.assertEqual(res1['status'], res2['status'])
        asyncio.run(_run())

    def test_expiry_check(self):
        """Muddati o'tgan buyruq REJECTED bo'ladi"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            cmd = {
                "command_id": "cmd_exp",
                "tool_id": "system.status",
                "params": {},
                "nonce": "n_exp_1",
                "expires_at": time.time() - 100,
            }
            res = await executor.execute(cmd)
            self.assertEqual(res['status'], 'REJECTED')
            self.assertIn("EXPIRED", res.get('error', ''))
        asyncio.run(_run())

    def test_nonce_replay_blocked(self):
        """Bir xil nonce bilan ikkinchi buyruq REJECTED bo'ladi"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            future = time.time() + 300
            cmd1 = {
                "command_id": "cmd_n1",
                "tool_id": "system.status",
                "params": {},
                "nonce": "shared_nonce",
                "expires_at": future,
            }
            await executor.execute(cmd1)
            cmd2 = {
                "command_id": "cmd_n2",
                "tool_id": "system.status",
                "params": {},
                "nonce": "shared_nonce",
                "expires_at": future,
            }
            res2 = await executor.execute(cmd2)
            self.assertEqual(res2['status'], 'REJECTED')
            self.assertIn("REPLAY", res2.get('error', ''))
        asyncio.run(_run())

    def test_invalid_tool_rejected(self):
        """Mavjud bo'lmagan tool REJECTED"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            cmd = {
                "command_id": "cmd_inv",
                "tool_id": "non.existent.tool",
                "params": {},
                "nonce": "n_inv_1",
                "expires_at": time.time() + 300,
            }
            res = await executor.execute(cmd)
            self.assertEqual(res['status'], 'REJECTED')
            self.assertIn("INVALID_TOOL", res.get('error', ''))
        asyncio.run(_run())

    def test_confirmation_required(self):
        """Tasdiqlash talab qiladigan tool tasdiqlanmasa REJECTED"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            cmd = {
                "command_id": "cmd_conf",
                "tool_id": "power.restart",
                "params": {},
                "nonce": "n_conf_1",
                "expires_at": time.time() + 300,
                "confirmation_status": "pending",
            }
            res = await executor.execute(cmd)
            self.assertEqual(res['status'], 'REJECTED')
            self.assertIn("CONFIRMATION", res.get('error', ''))
        asyncio.run(_run())

    def test_successful_execution(self):
        """system.status muvaffaqiyatli bajarilishi kerak"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            cmd = {
                "command_id": "cmd_succ",
                "tool_id": "system.status",
                "params": {},
                "nonce": "n_succ_1",
                "expires_at": time.time() + 300,
            }
            res = await executor.execute(cmd)
            self.assertEqual(res['status'], 'SUCCEEDED')
            self.assertIsNotNone(res.get('result'))
        asyncio.run(_run())

    def test_result_sanitization(self):
        """Natija hajmi chegaralangan"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor(max_result_size=100)
            cmd = {
                "command_id": "cmd_san",
                "tool_id": "system.status",
                "params": {},
                "nonce": "n_san_1",
                "expires_at": time.time() + 300,
            }
            res = await executor.execute(cmd)
            # Result should be within bounds
            result_json = json.dumps(res.get('result', {}))
            self.assertTrue(len(result_json) <= 200 or res.get('result', {}).get('_truncated', False))
        asyncio.run(_run())

    def test_stats(self):
        """Execution counter oshishi kerak"""
        if not RemoteCommandExecutor: self.skipTest("Module not found")
        async def _run():
            executor = RemoteCommandExecutor()
            self.assertEqual(executor._execution_count, 0)
            cmd = {
                "command_id": "cmd_stat",
                "tool_id": "system.status",
                "params": {},
                "nonce": "n_stat_1",
                "expires_at": time.time() + 300,
            }
            await executor.execute(cmd)
            self.assertEqual(executor._execution_count, 1)
        asyncio.run(_run())


# ================================================================
# 4. COMMAND QUEUE MANAGER TESTS (8 tests)
# ================================================================
class TestCommandQueueManager(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def _get_mgr(self):
        return CommandQueueManager()

    def test_submit_command(self):
        """Buyruq PENDING holat bilan yaratiladi"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, token = mgr.submit_command("dev1", "user1", "system.status", {})
        self.assertEqual(cmd.state, CommandState.PENDING)
        self.assertIsNone(token)
        self.assertTrue(cmd.command_id)

    def test_submit_with_confirmation(self):
        """Tasdiqlash talab qiladigan buyruq ConfirmationToken qaytaradi"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, token = mgr.submit_command(
            "dev1", "user1", "power.restart", {},
            requires_confirmation=True, risk_level='high'
        )
        self.assertIsNotNone(token)
        self.assertEqual(cmd.state, CommandState.AWAITING_CONFIRMATION)
        self.assertTrue(token.token)

    def test_confirm_command(self):
        """Valid token bilan buyruqni tasdiqlash"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, token = mgr.submit_command(
            "dev1", "user1", "power.restart", {},
            requires_confirmation=True, risk_level='high'
        )
        success, msg = mgr.confirm_command(cmd.command_id, token.token, "user1")
        self.assertTrue(success, f"Confirm failed: {msg}")
        self.assertEqual(cmd.state, CommandState.CONFIRMED)

    def test_confirm_expired_token(self):
        """Muddati o'tgan token rad etilishi kerak"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, token = mgr.submit_command(
            "dev1", "user1", "power.restart", {},
            requires_confirmation=True, risk_level='high'
        )
        # Force token expiry
        token.expires_at = time.time() - 100
        success, msg = mgr.confirm_command(cmd.command_id, token.token, "user1")
        self.assertFalse(success)

    def test_cancel_command(self):
        """Kutilayotgan buyruqni bekor qilish"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, _ = mgr.submit_command("dev1", "user1", "system.status", {})
        success, msg = mgr.cancel_command(cmd.command_id, "user1")
        self.assertTrue(success, f"Cancel failed: {msg}")
        self.assertEqual(cmd.state, CommandState.CANCELLED)

    def test_get_pending_commands(self):
        """Pending buyruqlar ro'yxati qaytadi va DISPATCHED deb belgilanadi"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        mgr.submit_command("dev1", "user1", "system.status", {})
        mgr.submit_command("dev1", "user1", "system.info", {})
        pending = mgr.get_pending_commands("dev1")
        self.assertEqual(len(pending), 2)
        # After dispatch, should be empty
        pending2 = mgr.get_pending_commands("dev1")
        self.assertEqual(len(pending2), 0)

    def test_record_result(self):
        """Natijani saqlash SUCCEEDED/FAILED holatga o'tkazadi"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, _ = mgr.submit_command("dev1", "user1", "system.status", {})
        mgr.get_pending_commands("dev1")  # dispatch it
        success = mgr.record_result(cmd.command_id, {"success": True, "data": {"status": "ok"}})
        self.assertTrue(success)
        self.assertEqual(cmd.state, CommandState.SUCCEEDED)

    def test_device_history(self):
        """Tugallangan buyruqlar tarixda ko'rinadi"""
        if not CommandQueueManager: self.skipTest("Module not found")
        mgr = self._get_mgr()
        cmd, _ = mgr.submit_command("dev1", "user1", "system.status", {})
        mgr.get_pending_commands("dev1")
        mgr.record_result(cmd.command_id, {"success": True})
        history = mgr.get_device_history("dev1")
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[-1]['command_id'], cmd.command_id)


# ================================================================
# 5. PHASE 46 INTEGRATION TESTS (4 tests)
# ================================================================
class TestPhase46Integration(unittest.TestCase):
    def setUp(self):
        self._orig_env = dict(os.environ)
        os.environ.pop('MIKASA_REQUIRE_AUTH', None)
        os.environ.pop('SUPABASE_URL', None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        _reset_singletons()

    def test_remote_tool_registry_has_15_tools(self):
        """RemoteToolRegistry 15 ta tool ro'yxatdan o'tgan"""
        if not RemoteToolRegistry: self.skipTest("Module not found")
        reg = RemoteToolRegistry.get_default_instance()
        tool_count = len(reg._tools)
        self.assertEqual(tool_count, 15, f"Expected 15 tools, got {tool_count}")

    def test_phase46_event_types_exist(self):
        """Barcha 14 ta Phase 46 event type mavjud"""
        if not RemoteEventType: self.skipTest("Module not found")
        expected_events = [
            "REMOTE_COMMAND_SUBMITTED", "REMOTE_COMMAND_DISPATCHED",
            "REMOTE_COMMAND_CONFIRMED", "REMOTE_COMMAND_REJECTED",
            "REMOTE_COMMAND_SUCCEEDED", "REMOTE_COMMAND_FAILED",
            "REMOTE_COMMAND_TIMEOUT", "REMOTE_COMMAND_EXPIRED",
            "REMOTE_COMMAND_CANCELLED", "REMOTE_COMMAND_REPLAY_BLOCKED",
            "REMOTE_CONFIRMATION_REQUESTED", "REMOTE_CONFIRMATION_ACCEPTED",
            "REMOTE_CONFIRMATION_EXPIRED", "REMOTE_PERMISSION_DENIED",
        ]
        for evt in expected_events:
            self.assertTrue(
                hasattr(RemoteEventType, evt),
                f"RemoteEventType.{evt} mavjud emas"
            )

    def test_tool_definition_extended(self):
        """RemoteToolDefinition yangi Phase 46 maydonlariga ega"""
        if not RemoteToolDefinition: self.skipTest("Module not found")
        td = RemoteToolDefinition(
            tool_id="test.tool",
            name="Test",
            description="Test tool",
            required_permission="test.perm"
        )
        self.assertTrue(hasattr(td, 'input_schema'))
        self.assertTrue(hasattr(td, 'output_schema'))
        self.assertTrue(hasattr(td, 'timeout'))
        self.assertTrue(hasattr(td, 'category'))
        self.assertTrue(hasattr(td, 'max_result_size'))
        self.assertEqual(td.timeout, 10.0)
        self.assertEqual(td.category, "general")
        self.assertEqual(td.max_result_size, 65536)

    def test_ast_security_scan(self):
        """agent/tools.py va agent/executor.py da eval/exec/os.system/shell=True yo'q"""
        base_dir = BASE_DIR
        files_to_scan = [
            os.path.join(base_dir, "agent", "tools.py"),
            os.path.join(base_dir, "agent", "executor.py"),
        ]
        for file_path in files_to_scan:
            if not os.path.exists(file_path):
                continue
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        self.assertNotIn(
                            node.func.id, ["eval", "exec"],
                            f"{node.func.id}() topildi: {file_path}:{node.lineno}"
                        )
                    elif isinstance(node.func, ast.Attribute):
                        if (node.func.attr == "system" and
                            isinstance(node.func.value, ast.Name) and
                            node.func.value.id == "os"):
                            self.fail(f"os.system() topildi: {file_path}:{node.lineno}")
                if isinstance(node, ast.keyword) and node.arg == "shell":
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        self.fail(f"shell=True topildi: {file_path}:{node.lineno}")


if __name__ == '__main__':
    unittest.main()
