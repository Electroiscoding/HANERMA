from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import time
import subprocess
import os
import asyncio
import logging

try:
    import grpc
    from src.hanerma.core.rpc import hanerma_hub_pb2
    from src.hanerma.core.rpc import hanerma_hub_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False
    logging.getLogger(__name__).warning("gRPC stubs not found. DistributedFleetRuntime will fail.")

logger = logging.getLogger(__name__)

class RuntimeEnvironment(ABC):
    """Base interface for all CUA topologies."""

    @abstractmethod
    async def click(self, x: int, y: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def type_text(self, text: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def take_screenshot(self) -> Dict[str, Any]:
        pass

class LocalRuntime(RuntimeEnvironment):
    """Topology Alpha: Single-Agent, Single-VM. Uses direct OS buffer."""
    def __init__(self):
        try:
            import pyautogui
            import mss
            self.pyautogui = pyautogui
            self.mss = mss.mss()
        except ImportError:
            logger.warning("pyautogui or mss not found. LocalRuntime will fail.")
            self.pyautogui = None
            self.mss = None

    async def click(self, x: int, y: int) -> Dict[str, Any]:
        if not self.pyautogui:
            raise RuntimeError("pyautogui not available")
        self.pyautogui.click(x, y)
        return {"success": True, "action": "click", "x": x, "y": y}

    async def type_text(self, text: str) -> Dict[str, Any]:
        if not self.pyautogui:
            raise RuntimeError("pyautogui not available")
        self.pyautogui.typewrite(text)
        return {"success": True, "action": "type", "text": text}

    async def take_screenshot(self) -> Dict[str, Any]:
        if not self.mss:
            raise RuntimeError("mss not available")

        timestamp = int(time.time())
        filename = f"/tmp/hanerma_local_{timestamp}.png"

        monitor = self.mss.monitors[1]
        sct_img = self.mss.grab(monitor)

        import mss.tools
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)

        return {"success": True, "path": filename}

class VirtualFramebufferRuntime(RuntimeEnvironment):
    """Topology Beta: Multi-Agent, Single-VM. Uses Xvfb."""
    def __init__(self, display_num: int = 99):
        self.display_num = display_num
        self.display_str = f":{display_num}"

        self.xvfb_proc = subprocess.Popen(
            ["Xvfb", self.display_str, "-screen", "0", "1920x1080x24"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.env = os.environ.copy()
        self.env["DISPLAY"] = self.display_str
        time.sleep(1)

    def __del__(self):
        if hasattr(self, 'xvfb_proc') and self.xvfb_proc:
            self.xvfb_proc.terminate()

    async def click(self, x: int, y: int) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "xdotool", "mousemove", str(x), str(y), "click", "1",
            env=self.env
        )
        await proc.wait()
        return {"success": True, "display": self.display_str, "action": "click"}

    async def type_text(self, text: str) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "xdotool", "type", text,
            env=self.env
        )
        await proc.wait()
        return {"success": True, "display": self.display_str, "action": "type"}

    async def take_screenshot(self) -> Dict[str, Any]:
        timestamp = int(time.time())
        filename = f"/tmp/hanerma_xvfb_{self.display_num}_{timestamp}.png"
        proc = await asyncio.create_subprocess_exec(
            "import", "-window", "root", filename,
            env=self.env
        )
        await proc.wait()
        return {"success": True, "path": filename}

class MultiplexedSSHRuntime(RuntimeEnvironment):
    """Topology Gamma: Single-Agent, Multi-VM."""
    def __init__(self, host: str, user: str):
        self.host = host
        self.user = user

    async def click(self, x: int, y: int) -> Dict[str, Any]:
        cmd = f"xdotool mousemove {x} {y} click 1"
        return await self._run_ssh(cmd)

    async def type_text(self, text: str) -> Dict[str, Any]:
        cmd = f"xdotool type '{text}'"
        return await self._run_ssh(cmd)

    async def take_screenshot(self) -> Dict[str, Any]:
        timestamp = int(time.time())
        filename = f"/tmp/hanerma_ssh_{self.host}_{timestamp}.png"
        cmd = f"import -window root {filename}"
        await self._run_ssh(cmd)
        return {"success": True, "path": filename, "host": self.host}

    async def _run_ssh(self, command: str) -> Dict[str, Any]:
        proc = await asyncio.create_subprocess_exec(
            "ssh", f"{self.user}@{self.host}", command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        return {
            "success": proc.returncode == 0,
            "stdout": stdout.decode() if stdout else "",
            "stderr": stderr.decode() if stderr else ""
        }

class DistributedFleetRuntime(RuntimeEnvironment):
    """Topology Delta: Multi-Agent, Multi-VM via gRPC Hub and Spoke."""
    def __init__(self, grpc_endpoint: str, agent_id: str):
        self.endpoint = grpc_endpoint
        self.agent_id = agent_id
        if not GRPC_AVAILABLE:
            raise RuntimeError("gRPC libraries not available.")

        self.channel = grpc.aio.insecure_channel(self.endpoint)
        self.stub = hanerma_hub_pb2_grpc.CUAHubStub(self.channel)

    async def click(self, x: int, y: int) -> Dict[str, Any]:
        req = hanerma_hub_pb2.ClickRequest(agent_id=self.agent_id, x=x, y=y)
        resp = await self.stub.Click(req)
        return {"success": resp.success, "error": resp.error_message}

    async def type_text(self, text: str) -> Dict[str, Any]:
        req = hanerma_hub_pb2.TypeRequest(agent_id=self.agent_id, text=text)
        resp = await self.stub.TypeText(req)
        return {"success": resp.success, "error": resp.error_message}

    async def take_screenshot(self) -> Dict[str, Any]:
        req = hanerma_hub_pb2.ScreenshotRequest(agent_id=self.agent_id)
        resp = await self.stub.TakeScreenshot(req)

        if not resp.success:
            return {"success": False, "error": resp.error_message}

        timestamp = int(time.time())
        filename = f"/tmp/hanerma_grpc_{self.agent_id}_{timestamp}.png"
        with open(filename, "wb") as f:
            f.write(resp.image_data)

        return {"success": True, "path": filename}

    async def close(self):
        await self.channel.close()
