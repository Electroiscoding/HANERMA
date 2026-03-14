#!/usr/bin/env python3
"""
HANERMA Zero-Resistance Onboarding
The 1-Minute Rule: pip install → running multi-agent swarm in < 60 seconds
BYOM Strategy: Switzerland of AI - works with Ollama, OpenRouter, HuggingFace
"""

import os
import sys
import time
import json
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path


class ZeroResistanceOnboarding:
    """
    Ultra-fast onboarding system for HANERMA.
    Gets developers from pip install to running swarm in under 60 seconds.
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.steps_completed = []
        self.model_registry = self._initialize_model_registry()
        
    def _initialize_model_registry(self) -> Dict[str, Any]:
        """Initialize the Switzerland model registry."""
        return {
            "local": {
                "name": "Ollama (Local)",
                "endpoint": "http://localhost:11434",
                "models": ["llama3", "mistral", "qwen", "codellama"],
                "privacy": "100%",
                "setup_time": "< 30s",
                "priority": 1
            },
            "openrouter": {
                "name": "OpenRouter (Multi-Provider)",
                "endpoint": "https://openrouter.ai/api/v1",
                "models": ["anthropic/claude-3", "openai/gpt-4", "google/gemini-pro"],
                "privacy": "Provider-dependent",
                "setup_time": "< 60s",
                "priority": 2
            },
            "huggingface": {
                "name": "HuggingFace (Open Models)",
                "endpoint": "https://api-inference.huggingface.co",
                "models": ["microsoft/DialoGPT-medium", "meta-llama/Llama-2-70b"],
                "privacy": "Model-dependent",
                "setup_time": "< 45s",
                "priority": 3
            }
        }
    
    def log_step(self, step_name: str, details: str = ""):
        """Log onboarding step with timing."""
        elapsed = time.time() - self.start_time
        self.steps_completed.append({
            "step": step_name,
            "details": details,
            "elapsed": f"{elapsed:.1f}s"
        })
        print(f"[{elapsed:.1f}s] {step_name}")
        if details:
            print(f"         {details}")
    
    def check_prerequisites(self) -> bool:
        """Check if prerequisites are met."""
        self.log_step("Checking prerequisites")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ required")
            return False
        
        # Check pip
        try:
            subprocess.run([sys.executable, "-m", "pip", "--version"], 
                         capture_output=True, check=True)
        except:
            print("❌ pip not available")
            return False
        
        self.log_step("Prerequisites OK", f"Python {sys.version.split()[0]}")
        return True
    
    def auto_detect_models(self) -> List[str]:
        """Auto-detect available models."""
        self.log_step("Auto-detecting models")
        
        available_models = []
        
        # Check Ollama
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [model["name"] for model in response.json().get("models", [])]
                available_models.extend([f"ollama:{model}" for model in models])
                self.log_step("Ollama detected", f"{len(models)} models")
        except:
            self.log_step("Ollama not running", "Install with: ollama pull llama3")
        
        # Check environment variables for API keys
        if os.getenv("OPENROUTER_API_KEY"):
            available_models.append("openrouter:claude-3")
            self.log_step("OpenRouter API key found")
        
        if os.getenv("HUGGINGFACE_API_KEY"):
            available_models.append("huggingface:llama-2-70b")
            self.log_step("HuggingFace API key found")
        
        return available_models
    
    def quick_start(self, prompt: str = "Hello world", model: str = "auto") -> Dict[str, Any]:
        """
        Quick start HANERMA in under 60 seconds.
        """
        self.log_step("🚀 Starting HANERMA Quick Start")
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            return {"success": False, "error": "Prerequisites not met"}
        
        # Step 2: Auto-detect models
        available_models = self.auto_detect_models()
        
        # Step 3: Initialize HANERMA with minimal config
        self.log_step("Initializing HANERMA")
        
        try:
            # Import HANERMA
            import hanerma
            
            # Create Natural API instance
            app = hanerma.Natural(
                prompt=prompt,
                model=model if model != "auto" else None,
                style_adaptation=False  # Disable for speed
            )
            
            self.log_step("HANERMA initialized", f"Model: {model}")
            
            # Step 4: Execute the swarm
            self.log_step("🐝 Running multi-agent swarm")
            
            start_time = time.time()
            result = app.run()
            execution_time = time.time() - start_time
            
            self.log_step("✅ Swarm execution complete", f"Time: {execution_time:.2f}s")
            
            total_time = time.time() - self.start_time
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "total_time": total_time,
                "steps": self.steps_completed,
                "available_models": available_models
            }
            
        except Exception as e:
            self.log_step("❌ Failed to start", str(e))
            return {
                "success": False,
                "error": str(e),
                "steps": self.steps_completed
            }
    
    def install_ollama_if_needed(self) -> bool:
        """Install Ollama if not present."""
        self.log_step("Checking Ollama installation")
        
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, check=True)
            self.log_step("Ollama already installed")
            return True
        except:
            self.log_step("Installing Ollama")
            
            # Install Ollama (simplified for cross-platform)
            try:
                if sys.platform == "darwin":
                    subprocess.run(["brew", "install", "ollama"], check=True)
                elif sys.platform == "linux":
                    subprocess.run(["curl", "-fsSL", "https://ollama.ai/install.sh", "|", "sh"], check=True)
                else:
                    self.log_step("Windows: Download from https://ollama.ai/download")
                    return False
                
                self.log_step("Ollama installed successfully")
                return True
            except:
                self.log_step("❌ Ollama installation failed")
                return False
    
    def pull_model_if_needed(self, model: str = "llama3") -> bool:
        """Pull a model if not available."""
        self.log_step(f"Checking model: {model}")
        
        try:
            # Check if model exists
            result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
            if model in result.stdout:
                self.log_step(f"Model {model} already available")
                return True
            
            # Pull model
            self.log_step(f"Pulling model: {model}")
            subprocess.run(["ollama", "pull", model], check=True)
            self.log_step(f"Model {model} pulled successfully")
            return True
        except:
            self.log_step(f"❌ Failed to pull model {model}")
            return False


def one_minute_demo():
    """
    Demonstrate the 1-Minute Rule in action.
    """
    print("🎯 HANERMA Zero-Resistance Onboarding Demo")
    print("=" * 50)
    print("Rule: Developer goes from pip install → running swarm in < 60s")
    print()
    
    onboard = ZeroResistanceOnboarding()
    
    # Quick demo with default settings
    result = onboard.quick_start(
        prompt="Write a simple Python function that adds two numbers",
        model="auto"
    )
    
    # Results
    total_time = result.get("total_time", 0)
    
    print("\n" + "=" * 50)
    print("📊 ONBOARDING RESULTS")
    print("=" * 50)
    
    for step in result.get("steps", []):
        print(f"[{step['elapsed']}] {step['step']}")
        if step.get("details"):
            print(f"         {step['details']}")
    
    print(f"\n⏱️  Total Time: {total_time:.1f}s")
    
    if total_time < 60:
        print("✅ 1-MINUTE RULE PASSED!")
        print("🚀 Developer is now running a multi-agent swarm!")
    else:
        print("⚠️  1-MINUTE RULE FAILED")
        print("❌ Took too long to onboard")
    
    return result


def show_model_registry():
    """Display the Switzerland model registry."""
    print("🇨🇭 HANERMA Model Registry - Switzerland of AI")
    print("=" * 60)
    
    onboard = ZeroResistanceOnboarding()
    registry = onboard.model_registry
    
    for provider, info in registry.items():
        print(f"\n📦 {info['name']}")
        print(f"   Endpoint: {info['endpoint']}")
        print(f"   Models: {', '.join(info['models'][:3])}...")
        print(f"   Privacy: {info['privacy']}")
        print(f"   Setup: {info['setup_time']}")
        print(f"   Priority: {info['priority']}")


def quick_setup_guide():
    """Show quick setup guide for different providers."""
    print("⚡ HANERMA Quick Setup Guide")
    print("=" * 40)
    
    print("\n🏠 LOCAL PRIVACY (Ollama):")
    print("   1. curl -fsSL https://ollama.ai/install.sh | sh")
    print("   2. ollama pull llama3")
    print("   3. python -c 'import hanerma; hanerma.Natural(\"Hello\").run()'")
    
    print("\n🌐 CLOUD FLEXIBILITY (OpenRouter):")
    print("   1. export OPENROUTER_API_KEY='your-key'")
    print("   2. python -c 'import hanerma; hanerma.Natural(\"Hello\", model=\"claude-3\").run()'")
    
    print("\n🤖 OPEN MODELS (HuggingFace):")
    print("   1. export HUGGINGFACE_API_KEY='your-key'")
    print("   2. python -c 'import hanerma; hanerma.Natural(\"Hello\", model=\"llama-2-70b\").run()'")
    
    print("\n🎯 AUTO-DETECT:")
    print("   python -c 'import hanerma; hanerma.Natural(\"Hello\").run()'")
    print("   # HANERMA automatically finds available models")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "demo":
            one_minute_demo()
        elif sys.argv[1] == "models":
            show_model_registry()
        elif sys.argv[1] == "guide":
            quick_setup_guide()
        else:
            print("Usage: python zero_resistance.py [demo|models|guide]")
    else:
        print("🎯 HANERMA Zero-Resistance Onboarding")
        print("Commands: demo, models, guide")
