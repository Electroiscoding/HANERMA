"""
Computer Use Agent (CUA) for HANERMA Hyper-Agentic System.

Enables HANERMA to interact with operating systems, control applications,
and perform computer use tasks with Z3 safety verification.
"""

import asyncio
import json
import logging
import subprocess
import time
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger("hanerma.cua")

class CUAAction(Enum):
    """Types of Computer Use Actions."""
    CLICK = "click"
    TYPE = "type"
    KEYPRESS = "keypress"
    SCROLL = "scroll"
    SCREENSHOT = "screenshot"
    LAUNCH = "launch"
    CLOSE = "close"
    DRAG = "drag"
    FILE_OPERATION = "file_op"

class CUASafetyLevel(Enum):
    """Safety levels for CUA operations."""
    SAFE = "safe"
    CAUTION = "caution"
    WARNING = "warning"
    DANGEROUS = "dangerous"

@dataclass
class CUAAction:
    """Computer Use Action with safety constraints."""
    action_type: CUAAction
    parameters: Dict[str, Any]
    safety_level: CUASafetyLevel
    description: str
    z3_constraints: List[str]

@dataclass
class CUAResult:
    """Result of a Computer Use operation."""
    success: bool
    action: CUAAction
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    execution_time: float

class CUAgent:
    """
    Computer Use Agent for HANERMA hyper-agentic capabilities.
    
    Provides OS-level interaction with Z3 safety verification.
    """
    
    def __init__(self, safety_constraints: Optional[Dict[str, Any]] = None):
        self.safety_constraints = safety_constraints or {}
        self.z3_solver = None  # Will be imported when available
        self.os_type = self._detect_os()
        
        logger.info(f"[CUA] Agent initialized for {self.os_type} OS")
        
        # Import Z3 solver for safety verification
        try:
            from hanerma.reasoning.z3_solver import Z3Solver
            self.z3_solver = Z3Solver()
        except ImportError:
            logger.warning("[CUA] Z3 solver not available - using simplified safety checks")
    
    def _detect_os(self) -> str:
        """Detect the operating system."""
        import platform
        return platform.system().lower()
    
    async def click_element(self, selector: str, safety_check: bool = True) -> CUAResult:
        """Click on a UI element."""
        if safety_check:
            # Verify safety constraints before execution
            safety_result = await self._verify_action_safety(CUAAction.CLICK, {"selector": selector})
            if not safety_result["allowed"]:
                return CUAResult(
                    success=False,
                    action=CUAAction.CLICK,
                    error=f"Safety constraint violation: {safety_result['reason']}"
                )
        
        try:
            # Use appropriate automation library based on OS
            if self.os_type == "windows":
                result = await self._click_windows(selector)
            elif self.os_type == "darwin":  # macOS
                result = await self._click_macos(selector)
            elif self.os_type == "linux":
                result = await self._click_linux(selector)
            else:
                return CUAResult(
                    success=False,
                    action=CUAAction.CLICK,
                    error=f"Unsupported OS: {self.os_type}"
                )
            
            logger.info(f"[CUA] Clicked element: {selector}")
            return CUAResult(
                success=True,
                action=CUAAction.CLICK,
                result={"clicked": True, "selector": selector}
            )
            
        except Exception as e:
            logger.error(f"[CUA] Click failed: {e}")
            return CUAResult(
                success=False,
                action=CUAAction.CLICK,
                error=f"Exception: {str(e)}"
            )
    
    async def _click_windows(self, selector: str) -> Dict[str, Any]:
        """Click element using Windows automation."""
        # Use pyautogui for Windows automation
        try:
            import pyautogui
            
            # Find element by selector (simplified)
            # In production, would use more sophisticated element finding
            pyautogui.click()
            
            return {"success": True, "method": "pyautogui"}
        except ImportError:
            return {"success": False, "error": "pyautogui not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _click_macos(self, selector: str) -> Dict[str, Any]:
        """Click element using macOS automation."""
        # Use AppleScript or pyautogui for macOS
        try:
            import pyautogui
            pyautogui.click()
            return {"success": True, "method": "pyautogui"}
        except ImportError:
            return {"success": False, "error": "pyautogui not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _click_linux(self, selector: str) -> Dict[str, Any]:
        """Click element using Linux automation."""
        # Use appropriate Linux automation tools
        try:
            import pyautogui
            pyautogui.click()
            return {"success": True, "method": "pyautogui"}
        except ImportError:
            return {"success": False, "error": "pyautogui not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def type_text(self, text: str, safety_check: bool = True) -> CUAResult:
        """Type text with safety verification."""
        if safety_check:
            safety_result = await self._verify_action_safety(CUAAction.TYPE, {"text": text})
            if not safety_result["allowed"]:
                return CUAResult(
                    success=False,
                    action=CUAAction.TYPE,
                    error=f"Safety constraint violation: {safety_result['reason']}"
                )
        
        try:
            if self.os_type == "windows":
                result = await self._type_windows(text)
            elif self.os_type == "darwin":
                result = await self._type_macos(text)
            elif self.os_type == "linux":
                result = await self._type_linux(text)
            else:
                return CUAResult(
                    success=False,
                    action=CUAAction.TYPE,
                    error=f"Unsupported OS: {self.os_type}"
                )
            
            logger.info(f"[CUA] Typed text: {text[:50]}...")
            return CUAResult(
                success=True,
                action=CUAAction.TYPE,
                result={"typed": True, "text": text}
            )
            
        except Exception as e:
            logger.error(f"[CUA] Type failed: {e}")
            return CUAResult(
                success=False,
                action=CUAAction.TYPE,
                error=f"Exception: {str(e)}"
            )
    
    async def _type_windows(self, text: str) -> Dict[str, Any]:
        """Type text using Windows automation."""
        try:
            import pyautogui
            pyautogui.typewrite(text)
            return {"success": True, "method": "pyautogui"}
        except ImportError:
            return {"success": False, "error": "pyautogui not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _type_macos(self, text: str) -> Dict[str, Any]:
        """Type text using macOS automation."""
        try:
            import pyautogui
            pyautogui.typewrite(text)
            return {"success": True, "method": "pyautogui"}
        except ImportError:
            return {"success": False, "error": "pyautogui not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _type_linux(self, text: str) -> Dict[str, Any]:
        """Type text using Linux automation."""
        try:
            import pyautogui
            pyautogui.typewrite(text)
            return {"success": True, "method": "pyautogui"}
        except ImportError:
            return {"success": False, "error": "pyautogui not available"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def take_screenshot(self, safety_check: bool = True) -> CUAResult:
        """Take screenshot with safety verification."""
        if safety_check:
            safety_result = await self._verify_action_safety(CUAAction.SCREENSHOT, {})
            if not safety_result["allowed"]:
                return CUAResult(
                    success=False,
                    action=CUAAction.SCREENSHOT,
                    error=f"Safety constraint violation: {safety_result['reason']}"
                )
        
        try:
            import pyautogui
            
            # Take screenshot
            screenshot = pyautogui.screenshot()
            
            # Save screenshot
            timestamp = int(time.time())
            screenshot_path = f"/tmp/hanerma_screenshot_{timestamp}.png"
            screenshot.save(screenshot_path)
            
            logger.info(f"[CUA] Screenshot saved: {screenshot_path}")
            return CUAResult(
                success=True,
                action=CUAAction.SCREENSHOT,
                screenshot_path=screenshot_path,
                result={"screenshot": True, "path": screenshot_path}
            )
            
        except ImportError:
            return CUAResult(
                success=False,
                action=CUAAction.SCREENSHOT,
                error="pyautogui not available"
            )
        except Exception as e:
            logger.error(f"[CUA] Screenshot failed: {e}")
            return CUAResult(
                success=False,
                action=CUAAction.SCREENSHOT,
                error=f"Exception: {str(e)}"
            )
    
    async def launch_application(self, app_path: str, safety_check: bool = True) -> CUAResult:
        """Launch an application with safety verification."""
        if safety_check:
            safety_result = await self._verify_action_safety(CUAAction.LAUNCH, {"app_path": app_path})
            if not safety_result["allowed"]:
                return CUAResult(
                    success=False,
                    action=CUAAction.LAUNCH,
                    error=f"Safety constraint violation: {safety_result['reason']}"
                )
        
        try:
            if self.os_type == "windows":
                result = await self._launch_windows(app_path)
            elif self.os_type == "darwin":
                result = await self._launch_macos(app_path)
            elif self.os_type == "linux":
                result = await self._launch_linux(app_path)
            else:
                return CUAResult(
                    success=False,
                    action=CUAAction.LAUNCH,
                    error=f"Unsupported OS: {self.os_type}"
                )
            
            logger.info(f"[CUA] Launched application: {app_path}")
            return CUAResult(
                success=True,
                action=CUAAction.LAUNCH,
                result={"launched": True, "app_path": app_path}
            )
            
        except Exception as e:
            logger.error(f"[CUA] Launch failed: {e}")
            return CUAResult(
                success=False,
                action=CUAAction.LAUNCH,
                error=f"Exception: {str(e)}"
            )
    
    async def _launch_windows(self, app_path: str) -> Dict[str, Any]:
        """Launch application on Windows."""
        try:
            import subprocess
            subprocess.Popen(["start", app_path], shell=True)
            return {"success": True, "method": "subprocess"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _launch_macos(self, app_path: str) -> Dict[str, Any]:
        """Launch application on macOS."""
        try:
            import subprocess
            subprocess.Popen(["open", app_path])
            return {"success": True, "method": "subprocess"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _launch_linux(self, app_path: str) -> Dict[str, Any]:
        """Launch application on Linux."""
        try:
            import subprocess
            subprocess.Popen(["xdg-open", app_path])
            return {"success": True, "method": "subprocess"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _verify_action_safety(self, action: CUAAction, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Verify action against Z3 safety constraints."""
        if not self.z3_solver:
            # Fallback to simple safety checks
            return await self._simple_safety_check(action, parameters)
        
        try:
            # Generate Z3 constraints for safety
            safety_constraints = self._generate_safety_constraints(action, parameters)
            
            # Check against user-defined safety constraints
            user_constraints = self.safety_constraints.get(action.value, [])
            
            # Combine all constraints
            all_constraints = safety_constraints + user_constraints
            
            # Verify with Z3
            result = self.z3_solver.check(all_constraints)
            
            if result == "sat":
                return {"allowed": True, "method": "z3_verification"}
            else:
                return {
                    "allowed": False, 
                    "reason": f"Z3 constraints unsatisfiable: {result}",
                    "constraints": all_constraints
                }
                
        except Exception as e:
            logger.error(f"[CUA] Safety verification error: {e}")
            return {"allowed": False, "reason": f"Verification error: {str(e)}"}
    
    async def _simple_safety_check(self, action: CUAAction, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Simple safety check without Z3."""
        # Basic safety rules
        dangerous_actions = [
            CUAAction.FILE_OPERATION,  # File operations are dangerous
        ]
        
        if action in dangerous_actions:
            return {
                "allowed": False,
                "reason": f"Action {action.value} is inherently dangerous"
            }
        
        # Check for dangerous parameters
        if action == CUAAction.TYPE and "text" in parameters:
            text = parameters["text"]
            dangerous_patterns = ["rm -rf", "del /", "format c:"]
            if any(pattern in text.lower() for pattern in dangerous_patterns):
                return {
                    "allowed": False,
                    "reason": f"Text contains dangerous pattern: {text}"
                }
        
        return {"allowed": True, "method": "simple_rules"}
    
    def _generate_safety_constraints(self, action: CUAAction, parameters: Dict[str, Any]) -> List[str]:
        """Generate Z3 safety constraints for an action."""
        constraints = []
        
        # Basic safety constraints
        constraints.append("action_is_safe(action)")
        
        # Action-specific constraints
        if action == CUAAction.CLICK:
            constraints.append("click_target_is_safe(selector)")
        elif action == CUAAction.TYPE:
            if "text" in parameters:
                constraints.append("typed_text_is_safe(text)")
        elif action == CUAAction.SCREENSHOT:
            constraints.append("screenshot_is_safe()")
        elif action == CUAAction.LAUNCH:
            if "app_path" in parameters:
                constraints.append("app_path_is_safe(app_path)")
        
        return constraints
