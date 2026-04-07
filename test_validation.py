#!/usr/bin/env python3
"""Test validation for DeepSeek Home Assistant integration."""

import json
import os
import sys
from pathlib import Path

def validate_manifest():
    """Validate manifest.json."""
    print("🔍 Validating manifest.json...")
    
    manifest_path = Path("custom_components/deepseek/manifest.json")
    if not manifest_path.exists():
        print("❌ manifest.json not found")
        return False
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    required_fields = [
        "domain", "name", "codeowners", "config_flow",
        "documentation", "integration_type", "iot_class",
        "requirements", "version"
    ]
    
    for field in required_fields:
        if field not in manifest:
            print(f"❌ Missing required field: {field}")
            return False
    
    # Check specific values
    if manifest["domain"] != "deepseek":
        print("❌ Domain should be 'deepseek'")
        return False
    
    if not manifest["config_flow"]:
        print("❌ config_flow should be true")
        return False
    
    if "openai" not in str(manifest.get("requirements", [])):
        print("❌ Requirements should include 'openai'")
        return False
    
    print("✅ manifest.json is valid")
    return True

def validate_structure():
    """Validate integration structure."""
    print("\n🔍 Validating integration structure...")
    
    required_files = [
        "custom_components/deepseek/__init__.py",
        "custom_components/deepseek/manifest.json",
        "custom_components/deepseek/config_flow.py",
        "custom_components/deepseek/const.py",
        "custom_components/deepseek/conversation.py",
        "custom_components/deepseek/strings.json",
        "custom_components/deepseek/services.yaml",
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ Missing required file: {file_path}")
            return False
    
    print("✅ Integration structure is valid")
    return True

def validate_imports():
    """Validate Python imports."""
    print("\n🔍 Validating Python imports...")
    
    try:
        # Test importing the main module
        sys.path.insert(0, "custom_components/deepseek")
        
        # Check if we can import key modules
        import importlib
        
        modules_to_test = [
            ("__init__", ["DOMAIN"]),
            ("const", ["DOMAIN", "DEFAULT_MODEL", "MODELS"]),
        ]
        
        for module_name, expected_attrs in modules_to_test:
            try:
                module = importlib.import_module(f".{module_name}", package="custom_components.deepseek")
                for attr in expected_attrs:
                    if not hasattr(module, attr):
                        print(f"❌ Missing attribute {attr} in {module_name}")
                        return False
            except ImportError as e:
                print(f"❌ Failed to import {module_name}: {e}")
                return False
        
        print("✅ Python imports are valid")
        return True
        
    except Exception as e:
        print(f"❌ Import validation failed: {e}")
        return False
    finally:
        # Clean up sys.path
        if "custom_components/deepseek" in sys.path:
            sys.path.remove("custom_components/deepseek")

def validate_strings():
    """Validate strings.json."""
    print("\n🔍 Validating strings.json...")
    
    strings_path = Path("custom_components/deepseek/strings.json")
    if not strings_path.exists():
        print("❌ strings.json not found")
        return False
    
    with open(strings_path) as f:
        strings = json.load(f)
    
    required_sections = ["config", "options", "services"]
    for section in required_sections:
        if section not in strings:
            print(f"❌ Missing section in strings.json: {section}")
            return False
    
    print("✅ strings.json is valid")
    return True

def main():
    """Run all validations."""
    print("🚀 DeepSeek Home Assistant Integration Validation")
    print("=" * 50)
    
    # Change to the integration directory
    original_dir = os.getcwd()
    integration_dir = Path(__file__).parent
    
    try:
        os.chdir(integration_dir)
        
        validations = [
            validate_manifest,
            validate_structure,
            validate_imports,
            validate_strings,
        ]
        
        all_valid = True
        for validation in validations:
            if not validation():
                all_valid = False
        
        print("\n" + "=" * 50)
        if all_valid:
            print("🎉 All validations passed! Integration is ready.")
            print("\n📋 Next steps:")
            print("1. Test with Home Assistant dev container")
            print("2. Run: hassfest validate")
            print("3. Submit to HACS default repositories")
            return 0
        else:
            print("❌ Some validations failed. Please fix the issues above.")
            return 1
            
    finally:
        os.chdir(original_dir)

if __name__ == "__main__":
    sys.exit(main())