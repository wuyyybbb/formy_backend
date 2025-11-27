"""
Environment Variable Parser for Configuration Files

Supports parsing ${ENV_VAR} placeholders in configuration strings and YAML files.
"""
import os
import re
from typing import Any, Dict
import yaml


def parse_env_value(value: str) -> str:
    """
    Parse a string value and replace ${ENV_VAR} placeholders with environment variables.
    
    Args:
        value: String that may contain ${ENV_VAR} placeholders
        
    Returns:
        String with placeholders replaced by environment variable values
        
    Examples:
        >>> os.environ['API_URL'] = 'http://localhost:8000'
        >>> parse_env_value('${API_URL}/api')
        'http://localhost:8000/api'
        
        >>> parse_env_value('redis://${REDIS_HOST}:${REDIS_PORT}')
        'redis://localhost:6379'
    """
    if not isinstance(value, str):
        return value
    
    # Pattern to match ${VAR_NAME} or ${VAR_NAME:default_value}
    pattern = r'\$\{([^}:]+)(?::([^}]*))?\}'
    
    def replacer(match):
        env_var = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ''
        return os.getenv(env_var, default_value)
    
    return re.sub(pattern, replacer, value)


def parse_env_dict(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively parse a dictionary and replace all ${ENV_VAR} placeholders.
    
    Args:
        config: Dictionary that may contain ${ENV_VAR} placeholders in string values
        
    Returns:
        Dictionary with all placeholders replaced
    """
    if isinstance(config, dict):
        return {key: parse_env_dict(value) for key, value in config.items()}
    elif isinstance(config, list):
        return [parse_env_dict(item) for item in config]
    elif isinstance(config, str):
        return parse_env_value(config)
    else:
        return config


def load_yaml_with_env(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and parse all ${ENV_VAR} placeholders.
    
    Args:
        file_path: Path to YAML file
        
    Returns:
        Parsed configuration dictionary with environment variables resolved
        
    Example YAML:
        database:
          host: ${DB_HOST:localhost}
          port: ${DB_PORT:5432}
          url: postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}/${DB_NAME}
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_config = yaml.safe_load(f)
    
    return parse_env_dict(raw_config)


def validate_required_env_vars(required_vars: list) -> Dict[str, str]:
    """
    Validate that all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary of variable names and their values
        
    Raises:
        ValueError: If any required variable is not set
    """
    missing = []
    values = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            values[var] = value
    
    if missing:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing)}\n"
            f"Please set these variables before starting the application."
        )
    
    return values


def print_env_status(env_vars: list, show_values: bool = False):
    """
    Print status of environment variables (for debugging).
    
    Args:
        env_vars: List of environment variable names to check
        show_values: Whether to show actual values (default: False for security)
    """
    print("\n" + "="*60)
    print("🔐 Environment Variables Status")
    print("="*60)
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if show_values:
                # Mask sensitive values
                if any(sensitive in var.upper() for sensitive in ['KEY', 'SECRET', 'PASSWORD', 'TOKEN']):
                    display = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
                else:
                    display = value
                print(f"✅ {var}: {display}")
            else:
                print(f"✅ {var}: Set")
        else:
            print(f"❌ {var}: Not set")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    # Test examples
    import doctest
    doctest.testmod()
    
    # Example usage
    print("\nExample 1: Parse simple placeholder")
    os.environ['API_URL'] = 'http://localhost:8000'
    result = parse_env_value('${API_URL}/health')
    print(f"Input:  '${{API_URL}}/health'")
    print(f"Output: '{result}'")
    
    print("\nExample 2: Parse with default value")
    result = parse_env_value('${UNDEFINED_VAR:default_value}')
    print(f"Input:  '${{UNDEFINED_VAR:default_value}}'")
    print(f"Output: '{result}'")
    
    print("\nExample 3: Parse complex URL")
    os.environ['REDIS_HOST'] = 'localhost'
    os.environ['REDIS_PORT'] = '6379'
    result = parse_env_value('redis://${REDIS_HOST}:${REDIS_PORT}/0')
    print(f"Input:  'redis://${{REDIS_HOST}}:${{REDIS_PORT}}/0'")
    print(f"Output: '{result}'")

