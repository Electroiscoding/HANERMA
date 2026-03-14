#!/usr/bin/env python3
"""
HANERMA - Production Entry Point
APEX EDITION - Production-Grade Multi-Agent Intelligence System

This is the main entry point for HANERMA in production environments.
Provides both the 5-Line API and legacy compatibility.

Usage:
    python main.py "Build a web scraper"
    python main.py --legacy
    python main.py --help
"""

import sys
import argparse
from typing import Optional


def main():
    """Main entry point for HANERMA production system."""
    parser = argparse.ArgumentParser(
        prog="hanerma",
        description="HANERMA APEX Edition - Production Multi-Agent Intelligence System"
    )
    
    # Main execution
    parser.add_argument(
        "prompt", 
        nargs="?", 
        help="Natural language task description (5-Line API)"
    )
    
    # Configuration options
    parser.add_argument(
        "--model", 
        default="auto",
        help="Model to use (auto, llama3, mistral, etc.)"
    )
    
    parser.add_argument(
        "--style-adaptation",
        action="store_true",
        default=True,
        help="Enable user style adaptation"
    )
    
    parser.add_argument(
        "--no-style-adaptation",
        action="store_true",
        help="Disable user style adaptation"
    )
    
    # Legacy mode
    parser.add_argument(
        "--legacy",
        action="store_true",
        help="Enable legacy compatibility mode"
    )
    
    # Voice control
    parser.add_argument(
        "--voice",
        action="store_true",
        help="Enable voice control"
    )
    
    # verbosity
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    # Version
    parser.add_argument(
        "--version",
        action="version",
        version="HANERMA APEX Edition 1.0.0"
    )
    
    args = parser.parse_args()
    
    # Handle legacy mode
    if args.legacy:
        print("[HANERMA] 🔄 Legacy mode enabled")
        from hanerma import Legacy
        legacy = Legacy()
        
        if args.prompt:
            # Legacy execution
            result = legacy.run(args.prompt)
            print(f"[HANERMA] Legacy result: {result}")
        else:
            print("[HANERMA] Legacy mode active - use with prompt")
        
        return
    
    # Handle CLI commands without prompt
    if not args.prompt:
        print("[HANERMA] Use 'hanerma' CLI for full command suite:")
        print("  hanerma run 'prompt'     - Execute mission")
        print("  hanerma viz              - Launch dashboard")
        print("  hanerma deploy --prod     - Production deployment")
        print("  hanerma test --redteam   - Security testing")
        print("  hanerma listen           - Voice control")
        print("  hanerma --help          - Show all options")
        return
    
    # 5-Line API execution
    try:
        # Import and initialize
        import hanerma
        
        # Style adaptation setting
        style_adaptation = args.style_adaptation and not args.no_style_adaptation
        
        # Create Natural API instance
        app = hanerma.Natural(
            prompt=args.prompt,
            model=args.model,
            style_adaptation=style_adaptation
        )
        
        # Enable voice if requested
        if args.voice:
            app.voice(enable=True)
        
        # Set verbosity
        if args.verbose:
            print("[HANERMA] Verbose mode enabled")
        
        # Execute the pipeline
        print("[HANERMA] 🚀 Starting execution...")
        result = app.run()
        
        # Display results
        if result.get("success", True):
            print("[HANERMA] ✅ Execution completed successfully")
            if args.verbose:
                print(f"[HANERMA] Result: {result}")
        else:
            print("[HANERMA] ❌ Execution failed")
            print(f"[HANERMA] Error: {result.get('error', 'Unknown error')}")
            if args.verbose:
                print(f"[HANERMA] Traceback: {result.get('traceback', '')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("[HANERMA] ⏹  Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"[HANERMA] ❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def production_ready():
    """Check if system is production ready."""
    try:
        import hanerma
        print("[HANERMA] ✅ Production system ready")
        print(f"[HANERMA] Version: {hanerma.__version__}")
        print("[HANERMA] Features: 5-Line API, Legacy Compatibility, Full CLI Suite")
        return True
    except ImportError as e:
        print(f"[HANERMA] ❌ Production system not ready: {e}")
        return False


if __name__ == "__main__":
    # Check production readiness
    if not production_ready():
        sys.exit(1)
    
    # Run main application
    main()
